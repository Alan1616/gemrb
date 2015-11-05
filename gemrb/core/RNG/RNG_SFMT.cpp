#include "RNG_SFMT.h"
#include <climits>
#include <ctime>

#include "System/Logging.h"

// This is from gcc sources, namely from fixincludes/inclhack.def
// On C++11 systems, <cstdint> could be included instead.
#ifndef UINT64_MAX
#define UINT64_MAX (~(uint64_t)0)
#endif

/**
 * The constructor initializes the random number generator with a 32bit integer seed
 * based on a hashed value of the current timestamp.
 * The singleton implementation guarantees that the constructor is called only once,
 * which means that the RNG is seeded only once which means that it is ok to use the
 * timestamp for seeding (because it can only be used once per second).
 */
RNG_SFMT::RNG_SFMT() {
  time_t now = time(NULL);	// current time
  unsigned char *ptr = (unsigned char *) &now;	// type-punned pointer into now variable
  uint32_t seed = 0;
  
  for (size_t i = 0; i < sizeof(now); ++i ) {
    /* The actual value of a time_t may not be portable, so we compute a “hash” of the 
     * bytes in it using a multiply-and-add technique. The factor used for 
     * multiplication normally comes out as 257, a prime and therefore a good candidate.
     * According to Knuth the seed can be chosen arbitrarily, so whatever makes the
     * time_t value into a compatible integer, will work.
     */
    seed = seed * (UCHAR_MAX + 2u) + ptr[i];
  }
  
  sfmt_init_gen_rand(&sfmt, seed);
}

/**
 * This creates an instance of the singleton class RNG_SFMT. Call this instead of the
 * constructor.
 */
RNG_SFMT* RNG_SFMT::getInstance() {
  // This is the variable that makes the class singleton. So you better not change it ;-)
  static RNG_SFMT theInstance;
  return &theInstance;
}

/**
 * This method is the rand() equivalent which calls the cdf with proper bounds.
 *
 * It is possible to generate random numbers from [-min, +/-max] though the RNG uses
 * unsigned numbers only, so this wrapper handles some special cases for min and max.
 *
 * It is only necessary that the upper bound is larger or equal to the lower bound - with the exception
 * that someone wants something like rand() % -foo.
 */
unsigned int RNG_SFMT::rand(int min, int max) {
  /* If min is negative, it would be possible to calculate
   * cdf(0, max - min) + min
   * There has been no use for negative random numbers with rand() though, so it's treated as error.
   */
  if(min < 0) {
    GemRB::error("RNG", "Invalid bounds for RNG! Got min %d < 0!\n", min);
  }

  // For complete fairness and equal timing, this should be a roll, but let's skip it anyway
  if(min == max)
    return max;

  // Someone wants rand() % -foo, so we compute -rand(0, +foo)
  // This is the only time where min > max is (sort of) legal.
  // Not handling this will cause the application to crash.
  if(min == 0 && max < 0) {
    return -cdf(0, -max);
  }

  // No special cases are left, except !(min > max) which is caught in the cdf itself.
  return cdf(min, max);
}

/**
 * Much thought went into this, please read this comment before you modify the
 * code.
 * Let SFMT() be an alias for sfmt_genrand_uint64() aka SFMT's rand() function.
 *
 * SMFT() returns a uniformly distributed pseudorandom number 0 - UINT64_MAX.
 * As SFMT() operates on a limited integer range, it is a _discrete_ function.
 *
 * We want a random number from a given interval [min, max] though, so we need
 * to implement the (discrete) cumulative distribution function SFMT(min, max),
 * which returns a random number X from [min, max].
 *
 * This CDF is by formal definition:
 * SFMT(X; min, max) = (floor(X) - min + 1) / (max - min + 1)
 *
 * To get out the random variable, solve for X:
 * floor(X) = SFMT(X; min, max) * (max - min + 1) + min - 1
 * So this is, what random(min, max) should look like.
 * Problem: SFMT(X; min, max) * (max - min + 1) could produce an integer
 * overflow, so it is not safe.
 *
 * One solution is to divide the universe into buckets of equal size depending
 * on the range [min, max] and assign X to the bucket that contains the number
 * generated by SFMT(). This equals to modulo computation and is not satisfying:
 * If the buckets don't divide the universe equally, because the bucket size is
 * not a divisor of 2, there will be a range in the universe that is biased because
 * one bucket is too small thus will be chosen less equally!
 *
 * This is solved by selection sampling:
 * As SFMT() is assumed to be unbiased, we are allowed to ignore those random
 * numbers from SFMT() that would force us to have an unequal bucket and generate new
 * random numbers until one number fits into one of the other buckets.
 * This can be compared to an ideal six sided die that is rolled until only
 * sides 1-5 show up, while 6 represents something that you don't want. So you
 * basically roll a five sided die.
 *
 * Note: If you replace the SFMT RNG with some other rand() function in the
 * future, then you _need_ to change the UINT64_MAX constant to the largest possible
 * random number which can be created by the new rand() function. This value is often
 * defined in a RAND_MAX constant.
 * Otherwise you will probably skew the outcome of the rand() method or worsen
 * the performance of the application.
 *
 * In threaded environments check the method's code for information on mutexes!
 */
unsigned int RNG_SFMT::cdf(unsigned int min, unsigned int max) {
  // This all makes no sense if min > max, which should never happen.
  if (min > max) {
    GemRB::error("RNG", "Invalid bounds for RNG! Got min %d, max %d\n", min, max);
    // at this point, the method exits. No return value is needed, because
    // basically the exception itself is returned.
  }

  // First compute the diameter (aka size, length) of the [min, max] interval
  const unsigned int diameter = max - min + 1;

  // Compute how many buckets (each in size of the diameter) will fit into the
  // universe.
  // If the division has a remainder, the result is floored automatically.
  const uint64_t buckets = UINT64_MAX / diameter;

  // Compute the last valid random number. All numbers beyond have to be
  // ignored.
  // If there was no remainder in the previous step, limit is equal to
  // UINT64_MAX.
  const uint64_t limit = diameter * buckets;

  uint64_t rand;
  
  /**
   * To make the random number generation thread-safe, a mutex should be created
   * around the number generation. Outside of the loop of course, to avoid locking
   * overhead.
   * In this case replace the lock/unlock comment and you probably also want to use
   * the vectorized functions from SFMT to generate many random numbers at once.
   */

  /**** call mutex.lock() here ****/
  
  do {
    rand = sfmt_genrand_uint64(&sfmt);
  } while (rand >= limit);
  
  /**** call mutex.unlock() here ****/

  // Now determine the bucket containing the SFMT() random number and after
  // adding the lower bound, a random number from [min, max] can be returned.
  return (unsigned int)(rand / buckets + min);
}

