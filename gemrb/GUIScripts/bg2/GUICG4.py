# GemRB - Infinity Engine Emulator
# Copyright (C) 2003 The GemRB Project
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
#character generation, ability (GUICG4)
import GemRB
import GUICommon
import CommonTables
from ie_stats import *
from GUIDefines import *
from ie_restype import RES_2DA

AbilityWindow = 0
TextAreaControl = 0
DoneButton = 0
AbilityTable = 0
Abclasrq = 0
Abclsmod = 0
Abclasrq = 0
Abracerq = 0
PointsLeft = 0
Minimum = 0
Maximum = 0
Add = 0
KitIndex = 0
HasStrExtra = 0
MyChar = 0

def CalcLimits(Abidx):
	global Minimum, Maximum, Add

	Race = CommonTables.Races.FindValue (3, GemRB.GetPlayerStat (MyChar, IE_RACE) )
	RaceName = CommonTables.Races.GetRowName(Race)

	Minimum = 3
	Maximum = 18

	Race = Abracerq.GetRowIndex(RaceName)
	tmp = Abracerq.GetValue(Race, Abidx*2)
	if tmp != 0:
		Minimum = tmp

	tmp = Abracerq.GetValue(Race, Abidx*2+1)
	if tmp != 0:
		Maximum = tmp

	Add = Abracead.GetValue(Race, Abidx)
	Race = Abracead.GetRowIndex(RaceName)
	if Abclsmod:
		Add += Abclsmod.GetValue(KitIndex, Abidx)
	Minimum += Add
	Maximum += Add

	tmp = Abclasrq.GetValue(KitIndex, Abidx)
	if tmp != 0 and tmp > Minimum:
		Minimum = tmp

	if Minimum < 1:
		Minimum = 1
	if Maximum > 25:
		Maximum = 25

	return

def RollPress():
	global Minimum, Maximum, Add, HasStrExtra, PointsLeft
	global AllPoints18

	GemRB.SetVar("Ability",0)
	GemRB.SetVar("Ability -1",0)
	PointsLeft = 0
	SumLabel = AbilityWindow.GetControl(0x10000002)
	SumLabel.SetText("0")
	SumLabel.SetUseRGB(1)

	if HasStrExtra:
		if AllPoints18:
			e = 100
		else:
			e = GemRB.Roll(1,100,0)
	else:
		e = 0
	GemRB.SetVar("StrExtra", e)

	Total = 0
	while (Total < 75):
		Total = 0
		for i in range(6):
			dice = 3
			size = 5
			CalcLimits(i)
			v = GemRB.Roll(dice, size, Add+3)
			if v<Minimum:
				v = Minimum
			if v>Maximum:
				v = Maximum
			if AllPoints18:
				v = 18
			GemRB.SetVar("Ability "+str(i), v )
			Total += v

			Label = AbilityWindow.GetControl(0x10000003+i)
			if i==0 and v==18 and HasStrExtra:
				Label.SetText("18/"+str(e) )
			else:
				Label.SetText(str(v) )
			Label.SetUseRGB(1)

	# add a counter to the title
	SumLabel = AbilityWindow.GetControl (0x10000000)
	SumLabel.SetText(GemRB.GetString(11976) + ": " + str(Total))
	AllPoints18 = 0
	return

def GiveAll18(wIdx, key, mod):
	global AllPoints18
	if mod == 2 and key == 127:
		AllPoints18 = 1
		RollPress()
		return 1
	return 0

def OnLoad():
	global AbilityWindow, TextAreaControl, DoneButton
	global PointsLeft, HasStrExtra
	global AbilityTable, Abclasrq, Abclsmod, Abracerq, Abracead
	global KitIndex, Minimum, Maximum, MyChar
	global AllPoints18

	AllPoints18 = 0
	
	Abracead = GemRB.LoadTable("ABRACEAD")
	if GemRB.HasResource ("ABCLSMOD", RES_2DA):
		Abclsmod = GemRB.LoadTable ("ABCLSMOD")
	Abclasrq = GemRB.LoadTable("ABCLASRQ")
	Abracerq = GemRB.LoadTable("ABRACERQ")

	MyChar = GemRB.GetVar ("Slot")
	Kit = GUICommon.GetKitIndex (MyChar)
	ClassName = GUICommon.GetClassRowName (MyChar)
	if Kit == 0:
		KitName = ClassName
	else:
		#rowname is just a number, first value row what we need here
		KitName = CommonTables.KitList.GetValue(Kit, 0)

	#if the class uses the warrior table for saves, then it may have the extra strength
	HasStrExtra = CommonTables.Classes.GetValue(ClassName, "STREXTRA", GTV_INT)

	KitIndex = Abclasrq.GetRowIndex(KitName)

	GemRB.LoadWindowPack("GUICG", 640, 480)
	AbilityTable = GemRB.LoadTable("ability")
	AbilityWindow = GemRB.LoadWindow(4)
	AbilityWindow.SetKeyPressEvent (GiveAll18)

	RerollButton = AbilityWindow.GetControl(2)
	RerollButton.SetText(11982)
	StoreButton = AbilityWindow.GetControl(37)
	StoreButton.SetText(17373)
	RecallButton = AbilityWindow.GetControl(38)
	RecallButton.SetText(17374)

	BackButton = AbilityWindow.GetControl(36)
	BackButton.SetText(15416)
	BackButton.SetFlags (IE_GUI_BUTTON_CANCEL, OP_OR)
	DoneButton = AbilityWindow.GetControl(0)
	DoneButton.SetText(11973)
	DoneButton.SetFlags(IE_GUI_BUTTON_DEFAULT,OP_OR)
	DoneButton.SetState(IE_GUI_BUTTON_ENABLED)

	RollPress()
	StorePress()
	for i in range(6):
		Button = AbilityWindow.GetControl(i+30)
		Button.SetEvent(IE_GUI_BUTTON_ON_PRESS, JustPress)
		Button.SetEvent(IE_GUI_MOUSE_LEAVE_BUTTON, EmptyPress)
		Button.SetVarAssoc("Ability", i)

		Button = AbilityWindow.GetControl(i*2+16)
		Button.SetEvent(IE_GUI_BUTTON_ON_PRESS, LeftPress)
		Button.SetVarAssoc("Ability", i )

		Button = AbilityWindow.GetControl(i*2+17)
		Button.SetEvent(IE_GUI_BUTTON_ON_PRESS, RightPress)
		Button.SetVarAssoc("Ability", i )

	TextAreaControl = AbilityWindow.GetControl(29)
	TextAreaControl.SetText(17247)

	StoreButton.SetEvent(IE_GUI_BUTTON_ON_PRESS, StorePress)
	RecallButton.SetEvent(IE_GUI_BUTTON_ON_PRESS, RecallPress)
	RerollButton.SetEvent(IE_GUI_BUTTON_ON_PRESS, RollPress)
	DoneButton.SetEvent(IE_GUI_BUTTON_ON_PRESS, NextPress)
	BackButton.SetEvent(IE_GUI_BUTTON_ON_PRESS, BackPress)
	AbilityWindow.SetVisible(WINDOW_VISIBLE)
	GemRB.SetRepeatClickFlags(GEM_RK_DISABLE, OP_NAND)
	return

def RightPress():
	global PointsLeft

	Abidx = GemRB.GetVar("Ability")
	Ability = GemRB.GetVar("Ability "+str(Abidx) )
	CalcLimits(Abidx)
	GemRB.SetToken("MINIMUM",str(Minimum) )
	GemRB.SetToken("MAXIMUM",str(Maximum) )
	TextAreaControl.SetText(AbilityTable.GetValue(Abidx, 1) )
	if Ability<=Minimum:
		return
	GemRB.SetVar("Ability "+str(Abidx), Ability-1)
	PointsLeft = PointsLeft + 1
	GemRB.SetVar("Ability -1",PointsLeft)
	SumLabel = AbilityWindow.GetControl(0x10000002)
	SumLabel.SetText(str(PointsLeft) )
	Label = AbilityWindow.GetControl(0x10000003+Abidx)
	StrExtra = GemRB.GetVar("StrExtra")
	if Abidx==0 and Ability==19 and StrExtra:
		Label.SetText("18/"+str(StrExtra) )
	else:
		Label.SetText(str(Ability-1) )
	return

def JustPress():
	Abidx = GemRB.GetVar("Ability")
	Ability = GemRB.GetVar("Ability "+str(Abidx) )
	CalcLimits(Abidx)
	GemRB.SetToken("MINIMUM",str(Minimum) )
	GemRB.SetToken("MAXIMUM",str(Maximum) )
	TextAreaControl.SetText(AbilityTable.GetValue(Abidx, 1) )
	return

def LeftPress():
	global PointsLeft

	Abidx = GemRB.GetVar("Ability")
	Ability = GemRB.GetVar("Ability "+str(Abidx) )
	CalcLimits(Abidx)
	GemRB.SetToken("MINIMUM",str(Minimum) )
	GemRB.SetToken("MAXIMUM",str(Maximum) )
	TextAreaControl.SetText(AbilityTable.GetValue(Abidx, 1) )
	if PointsLeft == 0:
		return
	if Ability>=Maximum:  #should be more elaborate
		return
	GemRB.SetVar("Ability "+str(Abidx), Ability+1)
	PointsLeft = PointsLeft - 1
	GemRB.SetVar("Ability -1",PointsLeft)
	SumLabel = AbilityWindow.GetControl(0x10000002)
	SumLabel.SetText(str(PointsLeft) )
	Label = AbilityWindow.GetControl(0x10000003+Abidx)
	StrExtra = GemRB.GetVar("StrExtra")
	if Abidx==0 and Ability==17 and HasStrExtra==1:
		Label.SetText("18/%02d"%(StrExtra) )
	else:
		Label.SetText(str(Ability+1) )
	return

def EmptyPress():
	TextAreaControl = AbilityWindow.GetControl(29)
	TextAreaControl.SetText(17247)
	return

def StorePress():
	GemRB.SetVar("StoredStrExtra",GemRB.GetVar("StrExtra") )
	for i in range(-1,6):
		GemRB.SetVar("Stored "+str(i),GemRB.GetVar("Ability "+str(i) ) )
	return

def RecallPress():
	global PointsLeft

	e=GemRB.GetVar("StoredStrExtra")
	GemRB.SetVar("StrExtra",e)
	Total = 0
	for i in range(-1,6):
		v = GemRB.GetVar("Stored "+str(i) )
		Total += v
		GemRB.SetVar("Ability "+str(i), v)
		Label = AbilityWindow.GetControl(0x10000003+i)
		if i==0 and v==18 and HasStrExtra==1:
			Label.SetText("18/"+str(e) )
		else:
			Label.SetText(str(v) )

	PointsLeft = GemRB.GetVar("Ability -1")

	# add a counter to the title
	SumLabel = AbilityWindow.GetControl (0x10000000)
	SumLabel.SetText(GemRB.GetString(11976) + ": " + str(Total))
	return

def BackPress():
	if AbilityWindow:
		AbilityWindow.Unload()
	GemRB.SetNextScript("CharGen5")
	GemRB.SetVar("StrExtra",0)
	for i in range(-1,6):
		GemRB.SetVar("Ability "+str(i),0)  #scrapping the abilities
	GemRB.SetRepeatClickFlags(GEM_RK_DISABLE, OP_OR)
	return

def NextPress():
	if AbilityWindow:
		AbilityWindow.Unload()
	AbilityTable = GemRB.LoadTable ("ability")
	AbilityCount = AbilityTable.GetRowCount ()

	# print our diagnostic as we loop (so as not to duplicate)
	for i in range (AbilityCount):
		StatID = AbilityTable.GetValue (i, 3)
		StatName = AbilityTable.GetRowName (i)
		StatValue = GemRB.GetVar ("Ability "+str(i))
		GemRB.SetPlayerStat (MyChar, StatID, StatValue)
		print "\t",StatName,":\t", StatValue

	GemRB.SetPlayerStat (MyChar, IE_STREXTRA, GemRB.GetVar ("StrExtra"))
	print "\tSTREXTRA:\t",GemRB.GetVar ("StrExtra")

	GemRB.SetRepeatClickFlags(GEM_RK_DISABLE, OP_OR)
	GemRB.SetNextScript("CharGen6")
	return
