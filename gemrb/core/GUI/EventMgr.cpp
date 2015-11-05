/* GemRB - Infinity Engine Emulator
 * Copyright (C) 2003 The GemRB Project
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.

 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 *
 */

#include "GUI/EventMgr.h"

#include "globals.h"
#include "win32def.h"

namespace GemRB {

unsigned long EventMgr::DCDelay = 250;
unsigned long EventMgr::RKDelay = 250;
bool EventMgr::TouchInputEnabled = true;

std::map<int, EventMgr::EventCallback*> EventMgr::HotKeys = std::map<int, EventMgr::EventCallback*>();

EventMgr::EventMgr(void)
{
	dc_time = 0;
	rk_flags = GEM_RK_DISABLE;
}

EventMgr::~EventMgr()
{
	std::vector<EventCallback*>::iterator it = tapsToDelete.begin();
	for (; it != tapsToDelete.end(); ++it) {
		delete *it;
	}
}

unsigned long EventMgr::GetRKDelay()
{
	if (rk_flags&GEM_RK_DISABLE) return (unsigned long) ~0;
	if (rk_flags&GEM_RK_DOUBLESPEED) return RKDelay/2;
	if (rk_flags&GEM_RK_QUADRUPLESPEED) return RKDelay/4;
	return RKDelay;
}

unsigned long EventMgr::SetRKFlags(unsigned long arg, unsigned int op)
{
	SetBits(rk_flags, arg, op);
	return rk_flags;
}

bool EventMgr::ButtonState(unsigned short btn) const
{
	return mouseButtonFlags.test(btn);
}

bool EventMgr::MouseDown() const
{
	return mouseButtonFlags.any();
}

void EventMgr::AddEventTap(EventCallback* cb, Event::EventType type)
{
	if (type == static_cast<Event::EventType>(-1)) {
		int t = Event::MouseMove;
		for (; t <= Event::KeyDown; t++) {
			taps.insert(std::make_pair(static_cast<Event::EventType>(t), cb));
		}
	} else {
		taps.insert(std::make_pair(type, cb));
	}
	tapsToDelete.push_back(cb);
}

void EventMgr::DispatchEvent(Event& e)
{
	// TODO: for mouse events: check double click delay and set if repeat
	// TODO: for key events: check repeat key delay and set if repeat

	// first check for hot key listeners
	if (IS_KEY_EVENT(e)) {
		int flags = e.mod << 16;
		flags |= e.keyboard.keycode;

		std::map<int, EventCallback*>::const_iterator hit;
		hit = HotKeys.find(flags);
		if (hit != HotKeys.end()) {
			EventCallback* cb = (*hit).second;
			if ((*cb)(e)) {
				return;
			}
		}
	} else {
		// set/clear the appropriate buttons
		mouseButtonFlags = e.mouse.buttonStates;
		mousePos = e.mouse.Pos();
	}

	// no hot keys or their listeners refused the event...
	std::pair<EventTaps::iterator, EventTaps::iterator> range;
	range = taps.equal_range(e.type);

	EventTaps::iterator it = range.first;
	for (; it != range.second; ++it) {
		EventCallback* cb = it->second;
		if ((*cb)(e)) {
			break; // this handler absorbed the event
		}
	}
}

bool EventMgr::RegisterHotKeyCallback(EventCallback* cb, KeyboardKey key, short mod)
{
	// TODO: return false if something already claimed this hot key combo?
	// or maybe should we allow mutliple registrations and iterate them until one accepts the event...
	int flags = mod << 16;
	flags |= key;
	HotKeys.insert(std::make_pair(flags, cb));
	return true;
}

inline Event InitializeEvent(int mod)
{
	Event e;
	e.mod = mod;
	e.time = GetTickCount();
	return e;
}

Event EventMgr::CreateMouseBtnEvent(const Point& pos, EventButton btn, bool down, int mod)
{
	Event e = InitializeEvent(mod);
	if (down) {
		e.type = Event::MouseDown;
		e.mouse.buttonStates |= 1 << (btn-1);
	} else {
		e.type = Event::MouseUp;
	}
	e.mouse.button = btn;
	e.mouse.x = pos.x;
	e.mouse.y = pos.y;
	e.isScreen = true;
	return e;
}

Event EventMgr::CreateMouseMotionEvent(const Point& pos, int mod)
{
	Event e = CreateMouseBtnEvent(pos, 0, mod);
	e.type = Event::MouseMove;
	return e;
}

Event EventMgr::CreateKeyEvent(KeyboardKey key, bool down, int mod)
{
	Event e = InitializeEvent(mod);
	e.type = (down) ? Event::KeyDown : Event::KeyUp;
	e.keyboard.keycode = key;
	e.isScreen = false;
	// TODO: need to translate the keycode for e.keyboard.character
	return e;
}

}
