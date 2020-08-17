import itertools

import abjad

from quicktions import Fraction as F

from mu.mel import ji
from mu.utils import infit

from mutools import attachments
from mutools import lily

from aml import globals_
from aml import tweaks as tw
from aml import versemaker

from aml.trackmaker import keyboard
from aml.trackmaker import strings


#####################################################
#            post processing functions              #
#####################################################

ARCO = attachments.StringContactPoint("arco")
PIZZ = attachments.StringContactPoint("pizzicato")


def _add_vl_intro(violin: lily.NOventLine, vm) -> None:
    violin[0].pitch = [ji.r(7, 9)]
    violin[0].string_contact_point = ARCO
    violin[0].volume = 0.6
    tw.crop(0, violin, F(1, 8), F(1, 8), F(3, 16), F(1, 16))
    violin[1].pitch = [ji.r(35, 32)]
    violin[2].pitch = [ji.r(64, 63)]
    violin[3].pitch = [ji.r(35, 32)]

    tw.add_glissando(1, (0, -1), violin)

    tw.crop(7, violin, F(1, 4), F(1, 8), F(1, 8), F(2, 16), F(2, 16))

    violin[7].pitch = [ji.r(3, 4)]
    violin[7].string_contact_point = PIZZ
    violin[7].volume = 1.3

    for n, p in (
        (8, ji.r(64, 63)),
        (9, ji.r(288, 245)),
        (10, ji.r(3, 2)),
        (11, ji.r(14, 9)),
    ):
        violin[n].pitch = [p + ji.r(1, 1)]
        violin[n].string_contact_point = ARCO
        violin[n].volume = 0.6

    tw.crop(9, violin, F(1, 16))
    violin[9].pitch = [ji.r(35, 32)]

    tw.crop(12, violin, F(1, 16))
    violin[13].pitch = [ji.r(288, 245)]
    # violin[13].pitch = [ji.r(288, 245)]

    violin[14].glissando = None
    tw.crop(14, violin, F(2, 8), F(1, 8), F(1, 8))
    violin[15].pitch = [ji.r(14, 9)]
    violin[15].ornamentation = None
    violin[16].ornamentation = None
    tw.rest(17, violin)

    # tw.eat(-2, -1, violin)
    violin[111].pitch = [ji.r(3, 4)]
    violin[111].string_contact_point = ARCO
    violin[111].volume = 0.3
    # print('violin', len(violin))

    # tw.crop(111, violin, F(1, 4))
    # tw.change_octave(112, -1, violin)
    tw.crop(110, violin, F(1, 4))
    violin[111].pitch = [ji.r(7, 9)]
    violin[111].volume = 0.16

    # tw.shorten(112, F(1, 4), violin)

    # tw.crop(112, violin, F(2, 4))
    # violin[113].pitch = [ji.r(8, 9)]


def _add_va_intro(viola: lily.NOventLine, vm) -> None:
    tw.crop(4, viola, F(1, 4), F(2, 4))
    viola[4].pitch = [ji.r(7, 8)]
    # viola[5].pitch = [ji.r(4, 7)]

    for n in (4, 5):
        viola[n].string_contact_point = PIZZ
        viola[n].volume = 1.3

    tw.rest(1, viola)
    viola[2].pitch = [ji.r(256, 245)]

    viola[101].pitch = [ji.r(7, 8)]
    viola[101].string_contact_point = ARCO
    viola[101].volume = 0.3
    tw.shorten(101, F(1, 2), viola)

    tw.crop(100, viola, F(1, 4))
    viola[101].pitch = [ji.r(2, 3)]

    # tw.eat(-2, -1, viola)
    # tw.crop(102, viola, F(2, 4))
    # viola[103].pitch = [ji.r(2, 3)]

    # print('viola', len(viola))


def _add_vc_intro(cello: lily.NOventLine, vm) -> None:
    tw.crop(3, cello, F(1, 4), F(2, 4))
    cello[3].pitch = [ji.r(7, 12)]
    # cello[4].pitch = [ji.r(256, 189).register(-1)]

    for n in (3, 4):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.3

    cello[-1].pitch = [ji.r(1, 4)]
    cello[-1].volume = 0.6
    cello[-1].string_contact_point = ARCO
    # tw.swap_duration(-1, -2, F(1, 4), cello)

    # print('cello', len(cello))

    tw.crop(91, cello, F(1, 8), position=False)
    cello[92].pitch = [ji.r(16, 15).register(-2)]
    tw.set_arco(92, cello)

    # tw.crop(94, cello, F(2, 4))
    # tw.change_octave(95, 1, cello)

    # tw.shorten(94, F(1, 4), cello)


def _add_left_intro(left: lily.NOventLine, vm) -> None:
    tw.crop(0, left, F(3, 8), F(1, 8))
    tw.add_kenong(1, left, ji.r(64, 63))
    left[1].volume = 1

    tw.crop(5, left, F(1, 8), F(4, 8), F(1, 8))
    tw.add_gong(5, left, ji.r(3, 2))
    tw.add_kenong(6, left, ji.r(64, 63))
    tw.add_kenong(7, left, ji.r(3, 2))

    tw.crop(4, left, F(1, 8), F(1, 8))
    tw.add_kenong(5, left, ji.r(72, 49))
    left[5].arpeggio = None

    tw.add_gong(-2, left, ji.r(35, 32))
    tw.add_gong(-1, left, ji.r(7, 6))
    tw.split(120, left, F(3, 4), F(1, 4))
    tw.add_kenong(121, left, ji.r(1, 1))
    left[121].volume = 0.4

    # print('left', len(left))


def _adapt_violin(violin: lily.NOventLine, vm) -> None:
    violin[0].acciaccatura = None

    tw.crop(3, violin, F(1, 4) + F(0, 8), F(1, 8), F(1, 8), F(2, 8))

    for n in (
        4,
        6,
    ):
        violin[n].volume = 1.5
        violin[n].string_contact_point = PIZZ

    violin[4].pitch = [ji.r(3, 4)]
    violin[6].pitch = [ji.r(35, 32)]

    # violin[7].pitch = [ji.r(3, 4)]
    violin[8].glissando = None
    tw.crop(8, violin, F(3, 16))
    violin[9].pitch = [ji.r(14, 9)]
    violin[10].pitch = [ji.r(3, 2)]

    tw.crop(14, violin, F(1, 8))
    violin[14].pitch = [ji.r(35, 32)]
    for n in (13, 14):
        violin[n].string_contact_point = PIZZ
        violin[n].volume = 1.6

    tw.crop(
        15,
        violin,
        F(5, 4) + F(2, 16),
        F(2, 16),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(2, 16),
        F(2, 16),
        F(1, 4),
        F(1, 4),
        F(1, 4),
        F(1, 4),
    )

    for n in (16, 17, 18, 20, 21, 22, 24, 26):
        if n == 17:
            violin[n].pitch = [ji.r(3, 4)]
        elif n == 21:
            violin[n].pitch = [ji.r(35, 64)]
        elif n == 22:
            violin[n].pitch = [ji.r(32, 63)]
        else:
            violin[n].pitch = [ji.r(7, 9)]

        violin[n].volume = 1.2
        violin[n].string_contact_point = PIZZ
        if n not in (24,):
            violin[n].pitch[0] += ji.r(2, 1)

        if n == 26:
            tw.add_acciaccatura(n, ji.r(3, 4), violin, False)

    violin[2].glissando = None
    tw.add_glissando(2, (0, 0, 1, 1), violin, durations=[F(1, 4), F(1, 8), F(1, 8)])

    tw.crop(3, violin, F(1, 8))
    violin[3].pitch = [ji.r(3, 2)]
    violin[3].string_contact_point = ARCO
    violin[3].volume = 0.4

    tw.crop(0, violin, F(3, 16))
    violin[1].pitch = [ji.r(35, 32)]
    violin[2].acciaccatura = None

    tw.crop(8, violin, F(1, 8))
    violin[9].pitch = [ji.r(3, 2)]

    tw.eat(32, 33, violin)
    violin[32].glissando = None
    tw.add_glissando(32, (0, -1, -1), violin, durations=[F(1, 8), F(1, 4)])
    tw.crop(33, violin, F(1, 4))
    violin[33].pitch = [ji.r(35, 32)]
    violin[33].volume = 0.54
    violin[33].string_contact_point = ARCO

    tw.eat(35, 36, violin)
    tw.swap_duration(37, 36, F(1, 4), violin)

    # tw.change_octave(36, 1, violin)
    tw.rest_many(tuple(range(39, 46)), violin)

    tw.crop(39, violin, F(3, 4), F(4, 4), F(1, 8), F(1, 8), F(1, 4))
    for n, r in ((39, (35, 32)), (40, (8, 9)), (42, (48, 35)), (43, (288, 245))):
        violin[n].pitch = [ji.r(*r)]
        violin[n].volume = 0.4
        violin[n].string_contact_point = ARCO

    tw.crop(5, violin, F(1, 8))

    violin[31].acciaccatura = None
    tw.crop(31, violin, F(1, 16), F(1, 16), F(1, 8))
    tw.crop(30, violin, F(1, 8), F(1, 16), F(1, 16), F(1, 8), F(1, 16), F(1, 16))
    for n, r in (
        (31, (128, 63)),
        (32, (14, 9)),
        (33, (3, 2)),
        (34, (288, 245)),
        (35, (3, 2)),
        (37, (3, 2)),
    ):
        violin[n].pitch = [ji.r(*r)]
        violin[n].volume = 0.4
        violin[n].string_contact_point = ARCO

    tw.rest(34, violin)

    violin[29].acciaccatura = None
    tw.crop(28, violin, F(1, 16), position=False)
    violin[29].pitch = [ji.r(3, 2)]
    violin[29].string_contact_point = PIZZ
    violin[29].volume = 0.7

    violin[44].prall = None
    tw.crop(44, violin, F(1, 8))
    violin[45].pitch = [ji.r(48, 35)]

    violin[40].glissando = None
    violin[40].pitch = [ji.r(48, 35)]

    tw.rest(62, violin)

    violin[60].acciaccatura = None
    violin[60].string_contact_point = PIZZ
    violin[60].volume = 1.4
    tw.prolong(60, F(1, 16) + F(3, 8), violin)

    tw.rest(59, violin)

    tw.rest_many(tuple(range(64, 67)), violin)

    tw.crop(63, violin, F(6, 4), F(4, 4), F(2, 4), F(3, 4))
    for n, p in ((64, ji.r(35, 32)), (65, ji.r(3, 4)), (66, ji.r(288, 245))):
        violin[n].pitch = [p]
        violin[n].volume = 0.45
        violin[n].string_contact_point = ARCO

    # tw.add_acciaccatura(47, ji.r(288, 245), violin, add_glissando=True)
    violin[47].acciaccatura = None

    tw.crop(46, violin, F(3, 8), F(1, 8))
    violin[47].pitch = [ji.r(48, 35)]
    violin[47].volume = 0.5
    violin[47].string_contact_point = ARCO

    tw.swap_duration(61, 60, F(1, 8), violin)
    tw.crop(60, violin, *([F(1, 8)] * 7))
    violin[60].pitch = [ji.r(35, 32).register(1)]
    violin[61].pitch = [ji.r(288, 245).register(1)]
    violin[62].pitch = [ji.r(288, 245).register(0)]
    violin[63].pitch = [ji.r(48, 35).register(0)]
    violin[64].pitch = [ji.r(35, 32).register(0)]
    violin[65].pitch = [ji.r(35, 32).register(1)]
    violin[66].pitch = [ji.r(3, 2).register(0)]

    tw.swap_duration(64, 63, F(1, 16), violin)

    tw.crop(59, violin, F(2, 16), F(2, 16), F(3, 16), F(1, 16))
    violin[60].pitch = [ji.r(288, 245)]
    violin[61].pitch = [ji.r(288, 245)]
    # violin[61].pitch = [ji.r(48, 35)]
    violin[62].pitch = [ji.r(288, 245).register(1)]

    for n in (60, 61, 62):
        violin[n].volume = 1.3
        violin[n].string_contact_point = PIZZ

    tw.prolong(69, F(1, 8), violin)
    tw.crop(70, violin, F(1, 8), F(1, 8) + F(3, 16))
    violin[71].pitch = [ji.r(48, 35)]
    violin[71].string_contact_point = ARCO
    violin[71].volume = 0.45

    violin[72].pitch = [ji.r(3, 4)]
    violin[72].string_contact_point = PIZZ
    violin[72].volume = 1.3

    tw.swap_duration(72, 71, F(1, 16), violin)

    tw.crop(71, violin, F(1, 4))
    violin[73].pitch = [ji.r(14, 9)]

    violin[73].pitch = list(p.copy() for p in violin[73].pitch)
    violin[73] = violin[73].copy()

    violin[72].pitch = [ji.r(8, 9)]

    tw.rest(60, violin)

    tw.crop(72, violin, F(1, 8))
    violin[73].pitch = [ji.r(3, 4)]

    tw.rest_many((74, 75, 76), violin)

    tw.prolong(73, F(2, 4), violin)
    tw.crop(73, violin, F(1, 8))
    violin[74].pitch = [ji.r(14, 9)]

    tw.postpone(72, F(1, 16), violin)

    violin[72].pitch = [ji.r(48, 35)]
    violin[72].string_contact_point = PIZZ
    violin[72].volume = 1.3

    tw.crop(48, violin, F(1, 8))
    violin[49].pitch = [ji.r(8, 9)]

    tw.crop(77, violin, F(3, 4))
    violin[78].pitch = [ji.r(8, 9)]
    violin[78].string_contact_point = ARCO
    violin[78].volume = 0.4

    tw.crop(78, violin, F(3, 8))
    violin[78].string_contact_point = PIZZ
    violin[78].volume = 1.3

    violin[83].ornamentation = None
    tw.prolong(83, F(2, 8), violin)
    tw.postpone(83, F(3, 8), violin)

    violin[79].pitch = [ji.r(48, 35)]
    violin[79].string_contact_point = PIZZ
    violin[79].volume = 1.3

    tw.crop(79, violin, F(1, 8), F(1, 8))
    tw.rest(80, violin)

    # tw.change_octave(79, 1, violin)

    tw.rest(82, violin)
    violin[82].string_contact_point = PIZZ
    violin[82].volume = 1.3
    tw.crop(82, violin, F(1, 4), F(1, 4), F(1, 8), F(1, 8), F(3, 16), F(1, 16))

    violin[83].pitch = [ji.r(288, 245)]
    violin[85].pitch = [ji.r(288, 245)]
    violin[86].pitch = [ji.r(3, 2)]
    violin[87].pitch = [ji.r(35, 32)]
    violin[88].pitch = [ji.r(3, 2)]

    tw.rest(82, violin)
    tw.rest(84, violin)

    # tw.postpone(88, F(1, 4), violin)
    tw.crop(88, violin, F(1, 4))
    violin[88].string_contact_point = PIZZ
    violin[88].volume = 1.3
    tw.change_octave(88, -1, violin)

    tw.crop(90, violin, F(1, 4))
    violin[90].string_contact_point = PIZZ
    violin[90].volume = 1.3
    # tw.change_octave(90, 1, violin)

    tw.eat(93, 92, violin)
    tw.crop(92, violin, F(3, 8))
    violin[92].string_contact_point = PIZZ
    violin[92].volume = 1.3

    tw.crop(91, violin, F(2, 8) + F(1, 16), F(1, 16), F(1, 8))
    violin[92].pitch = [ji.r(3, 2)]
    violin[93].pitch = [ji.r(7, 9)]

    for n in (92, 93, 94):
        violin[n].string_contact_point = PIZZ
        violin[n].volume = 1.3

    violin[95].string_contact_point = ARCO
    violin[95].volume = 0.4

    tw.swap_duration(94, 95, F(1, 8), violin)
    tw.crop(95, violin, F(1, 8))
    violin[95].pitch = [ji.r(8, 9)]

    tw.shorten(91, F(1, 16), violin)
    tw.crop(94, violin, F(1, 16))
    violin[95].pitch = [ji.r(8, 9)]


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    viola[0].pitch = [ji.r(4, 7)]
    tw.split_by_structure(0, 3, viola, vm, adapt_by_changed_structure=True)

    tw.rest(0, viola)
    tw.swap_duration(1, 0, F(1, 16), viola)

    for n in (1, 2):
        viola[n].volume = 0.6
        viola[n].string_contact_point = ARCO

    # viola[1].pitch = [ji.r(4, 7)]
    viola[1].pitch = [ji.r(4, 7)]
    viola[2].pitch = [ji.r(48, 49)]
    viola[5].pitch = [ji.r(7, 8)]

    tw.swap_duration(2, 3, F(1, 32), viola)

    tw.crop(6, viola, F(3, 16) + F(0, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8))

    for n in (
        7,
        9,
        10,
    ):
        viola[n].volume = 1.5
        viola[n].string_contact_point = PIZZ

    viola[7].pitch = [ji.r(7, 8)]
    viola[9].pitch = [ji.r(35, 24).register(-1)]
    viola[10].pitch = [ji.r(7, 8)]

    tw.crop(10, viola, F(1, 8))
    viola[11].pitch = [ji.r(2, 3)]
    viola[12].acciaccatura = None
    viola[13].pitch = [ji.r(7, 8)]

    for n in (11, 12, 13):
        viola[n].string_contact_point = ARCO
        viola[n].volume = 0.3

    tw.crop(17, viola, F(1, 16))
    viola[18].pitch = [ji.r(48, 49)]
    viola[18].volume = 1.5
    viola[18].string_contact_point = PIZZ

    viola[16].acciaccatura = None
    viola[16].volume = 0.3
    tw.crop(16, viola, F(1, 8))
    viola[16].ornamentation = None
    viola[17].pitch = [ji.r(2, 3)]

    tw.crop(23, viola, F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4))

    for n in (
        24,
        26,
        28,
        30,
    ):
        viola[n].volume = 1.5
        viola[n].string_contact_point = PIZZ

    viola[24].pitch = [ji.r(7, 8)]
    viola[26].pitch = [ji.r(35, 24).register(-1)]
    viola[28].pitch = [ji.r(4, 3).register(-1)]
    viola[30].pitch = [ji.r(35, 24).register(-1)]

    viola[31].pitch = [ji.r(7, 8)]
    tw.rest(41, viola)

    tw.crop(40, viola, F(1, 32) + F(3, 4), F(3, 4), F(4, 4), F(2, 4))
    for n, r in ((41, (35, 48)), (42, (2, 3)), (43, (256, 245))):
        viola[n].pitch = [ji.r(*r)]
        viola[n].volume = 0.4
        viola[n].string_contact_point = ARCO

    tw.crop(31, viola, F(1, 16))
    viola[31].pitch = [ji.r(35, 48)]
    viola[32].pitch = [ji.r(4, 5)]
    viola[33].pitch = [ji.r(7, 8)]

    tw.crop(30, viola, F(1, 4), F(3, 8), F(1, 8))
    viola[32].pitch = [ji.r(4, 7)]

    viola[32].volume = 0.4
    viola[32].string_contact_point = ARCO

    tw.rest(31, viola)

    viola[37].acciaccatura = None

    for n in range(32, 38):
        tw.change_octave(n, 1, viola)

    viola[38].ornamentation = None
    viola[38].glissando = None
    tw.shorten(38, F(1, 32), viola)
    tw.shorten(42, F(1, 32), viola)

    viola[48].pitch = [ji.r(35, 48)]
    viola[48].optional = None
    viola[48].choose = None

    viola[53].optional = None

    tw.crop(54, viola, F(3, 8), F(3, 4))
    viola[55].pitch = [ji.r(35, 48)]
    viola[55].volume = 1.4
    viola[55].string_contact_point = PIZZ

    tw.rest(53, viola)

    viola[44].volume = 0.4
    tw.crop(44, viola, F(3, 8))
    viola[44].pitch = [ji.r(7, 8)]

    tw.rest_many(tuple(range(66, 73)), viola)

    tw.crop(65, viola, F(1, 16) + F(1, 4), F(4, 4), F(2, 4), F(3, 4))
    for n, p in ((66, ji.r(35, 48)), (67, ji.r(4, 7)), (68, ji.r(48, 49))):
        viola[n].pitch = [p]
        viola[n].volume = 0.45
        viola[n].string_contact_point = ARCO

    tw.crop(43, viola, F(1, 16) + F(1, 8) + F(0, 16), F(1, 8), F(4, 16), F(1, 8))
    for n in (44, 45, 46, 47):
        viola[n].pitch = [ji.r(8, 7)]
        viola[n].volume = 0.6
        viola[n].string_contact_point = ARCO

    viola[44].pitch = [ji.r(48, 49)]
    viola[46].pitch = [ji.r(7, 8)]
    viola[47].pitch = [ji.r(2, 3)]

    tw.swap_duration(60, 59, F(1, 8), viola)
    tw.crop(59, viola, *([F(1, 8)] * 6))
    viola[59].pitch = [ji.r(7, 4).register(0)]
    viola[60].pitch = [ji.r(48, 49).register(-1)]
    viola[61].pitch = [ji.r(48, 49).register(-1)]
    viola[62].pitch = [ji.r(8, 7).register(-1)]
    viola[63].pitch = [ji.r(7, 8).register(-1)]
    viola[64].pitch = [ji.r(35, 24).register(-1)]
    viola[65].pitch = [ji.r(2, 3).register(-1)]

    tw.swap_duration(63, 62, F(1, 16), viola)

    tw.crop(58, viola, F(1, 16) + F(2, 16), F(2, 16), F(3, 16), F(1, 16))
    viola[59].pitch = [ji.r(48, 49).register(0)]
    viola[60].pitch = [ji.r(48, 49)]
    viola[61].pitch = [ji.r(48, 49).register(0)]

    for n in (59, 60, 61, 71):
        # for n in (59, 60, 61):
        viola[n].volume = 1.3
        viola[n].string_contact_point = PIZZ

    viola[71].ornamentation = None
    viola[71].acciaccatura = None
    tw.shorten(71, F(1, 8), viola)

    tw.crop(70, viola, F(1, 4))
    viola[71].pitch = [ji.r(8, 7)]
    viola[71].acciaccatura = None

    tw.add_acciaccatura(70, ji.r(2, 3), viola, add_glissando=True)

    tw.swap_duration(72, 71, F(1, 16), viola)

    tw.prolong(72, F(1, 8), viola)
    # tw.eat(72, 73, viola)

    tw.crop(45, viola, F(3, 16))
    viola[46].pitch = [ji.r(48, 49)]

    tw.swap_duration(43, 44, F(1, 8), viola)
    tw.swap_duration(45, 46, F(2, 16), viola)
    tw.eat(45, 46, viola)
    viola[47].volume = 0.3
    tw.crop(45, viola, F(1, 8))
    tw.rest(45, viola)

    viola[73].pitch = [ji.r(35, 48)]

    tw.crop(72, viola, F(2, 16))
    viola[73].pitch = [ji.r(4, 5)]
    tw.crop(74, viola, F(1, 8))
    viola[75].pitch = [ji.r(8, 5)]

    tw.rest_many((77, 78, 79, 80, 81), viola)

    tw.prolong(75, F(2, 4), viola)
    tw.crop(75, viola, F(1, 8))
    viola[76].pitch = [ji.r(35, 48)]

    tw.postpone(74, F(1, 16), viola)

    viola[74].pitch = [ji.r(4, 7)]
    viola[74].volume = 1.3
    viola[74].string_contact_point = PIZZ

    viola[73].pitch = [ji.r(2, 3)]
    viola[73].volume = 0.24

    tw.crop(78, viola, F(3, 4))
    viola[79].pitch = [ji.r(4, 5)]
    viola[79].string_contact_point = ARCO
    viola[79].volume = 0.4

    tw.crop(79, viola, F(3, 8))
    viola[79].string_contact_point = PIZZ
    viola[79].volume = 1.3

    tw.prolong(84, F(2, 8), viola)
    tw.postpone(84, F(3, 8), viola)

    viola[80].string_contact_point = PIZZ
    viola[80].volume = 1.3
    tw.crop(80, viola, F(1, 8), F(1, 8))
    tw.rest(81, viola)
    viola[82].pitch = [ji.r(8, 7)]

    viola[83].string_contact_point = PIZZ
    viola[83].volume = 1.3
    tw.crop(83, viola, F(1, 4), F(1, 4), F(1, 8), F(1, 8), F(3, 16), F(1, 16))
    viola[83].pitch = [ji.r(4, 7)]
    viola[85].pitch = [ji.r(8, 7)]
    viola[84].pitch = [ji.r(48, 49)]
    viola[86].pitch = [ji.r(48, 49)]
    viola[87].pitch = [ji.r(8, 7)]
    viola[88].pitch = [ji.r(7, 8)]
    tw.rest(89, viola)

    tw.crop(90, viola, F(1, 4))
    viola[90].string_contact_point = PIZZ
    viola[90].volume = 1.3

    tw.eat(93, 92, viola)
    tw.crop(92, viola, F(3, 8))
    viola[92].string_contact_point = PIZZ
    viola[92].volume = 1.3

    tw.crop(91, viola, F(2, 8) + F(1, 16), F(1, 16), F(1, 8))
    viola[92].pitch = [ji.r(8, 7)]
    viola[93].pitch = [ji.r(7, 8)]

    for n in (92, 93, 94):
        viola[n].string_contact_point = PIZZ
        viola[n].volume = 1.3

    viola[95].string_contact_point = ARCO
    viola[95].volume = 0.3

    tw.swap_duration(94, 95, F(1, 8), viola)
    tw.crop(95, viola, F(1, 8))
    viola[95].pitch = [ji.r(2, 3)]

    tw.shorten(91, F(1, 16), viola)
    tw.crop(94, viola, F(1, 16))
    viola[95].pitch = [ji.r(2, 3)]


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    for n in (0, 2):
        cello[n].string_contact_point = ARCO
        cello[n].volume = 0.5

    cello[0].pitch = [ji.r(256, 189).register(-1)]
    cello[1].pitch = [ji.r(72, 49).register(-1)]
    cello[1].acciaccatura = None
    cello[2].pitch = [ji.r(1, 1).register(0)]
    cello[3].pitch = [ji.r(7, 6).register(0)]

    tw.crop(4, cello, F(1, 8), F(1, 8), F(1, 8), F(2, 8))
    cello[5].pitch = [ji.r(7, 6).register(0)]
    cello[7].pitch = [ji.r(7, 6).register(-1)]

    for n in (
        5,
        7,
    ):
        cello[n].volume = 1.5
        cello[n].string_contact_point = PIZZ

    cello[8].pitch = [ji.r(16, 15).register(-1)]
    cello[8].volume = 0.4
    cello[8].string_contact_point = ARCO
    tw.split_by_structure(8, 3, cello, vm, adapt_by_changed_structure=True)
    tw.rest(8, cello)
    cello[10].pitch = [ji.r(7, 6).register(-1)]

    cello[13].string_contact_point = ARCO
    cello[13].optional = None
    cello[13].volume = 0.4
    cello[13].acciaccatura = None
    cello[14].volume = 0.4
    cello[14].string_contact_point = ARCO
    cello[14].pitch = [ji.r(8, 15)]
    tw.crop(14, cello, F(3, 16), position=False)
    cello[15].pitch = [ji.r(72, 49).register(-1)]
    cello[15].string_contact_point = PIZZ
    cello[15].volume = 1.5
    tw.split_by_structure(14, 2, cello, vm, adapt_by_changed_structure=True)
    tw.rest(15, cello)
    # tw.split_by_structure(14, cello)

    tw.swap_duration(13, 14, F(1, 16), cello)

    for n in (17, 18, 19):
        cello[n].pitch = [ji.r(7, 12)]
        cello[n].volume = 1.6

    tw.crop(
        20,
        cello,
        F(4, 4) + F(1, 8),
        F(1, 4),
        F(1, 4),
        F(1, 4),
        F(1, 4),
        F(1, 4),
        F(1, 4),
    )
    cello[21].pitch = [ji.r(7, 6).register(0)]
    cello[23].pitch = [ji.r(7, 6).register(-1)]
    cello[25].pitch = [ji.r(7, 6).register(-2)]
    cello[27].pitch = [ji.r(7, 6).register(-1)]

    for n in (
        21,
        23,
        25,
        27,
    ):
        cello[n].volume = 1.5
        cello[n].string_contact_point = PIZZ

    tw.change_octave(11, -1, cello)
    cello[11].glissando = None

    tw.crop(7, cello, F(1, 8))
    cello[8].pitch = [ji.r(7, 6).register(-2)]

    for n in (29, 30, 31):
        tw.change_octave(n, 1, cello)

    tw.rest(32, cello)
    tw.crop(32, cello, F(1, 16) + F(1, 4), F(2, 4), F(2, 4))

    cello[33].pitch = [ji.r(7, 12)]
    cello[34].pitch = [ji.r(7, 12)]

    for n in (33, 34):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.3

    tw.rest_many(tuple(range(36, 44)), cello)

    tw.crop(35, cello, F(3, 4), F(3, 4), F(4, 4), F(2, 4))
    for n, r in ((36, (7, 12)), (37, (16, 15)), (38, (384, 245 * 2))):
        cello[n].pitch = [ji.r(*r)]
        cello[n].volume = 0.4
        cello[n].string_contact_point = ARCO

    tw.crop(35, cello, F(1, 8), position=False)
    cello[36].pitch = [ji.r(1, 2)]
    cello[36].string_contact_point = ARCO
    cello[36].volume = 0.3

    tw.crop(28, cello, F(1, 4))
    tw.rest(29, cello)

    tw.crop(29, cello, F(3, 8), F(1, 8), F(1, 4))
    cello[30].pitch = [ji.r(3, 7)]
    cello[31].pitch = [ji.r(7, 24)]
    for n in (30, 31):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.4

    # tw.add_artifical_harmonic(30, ji.r(12, 7).register(-2), cello)

    cello[34].acciaccatura = None
    tw.crop(38, cello, F(1, 8))
    # tw.change_octave(39, -1, cello)
    cello[39].pitch = [ji.r(3, 7)]
    tw.swap_duration(32, 33, F(1, 8), cello)
    tw.change_octave(33, 1, cello)
    cello[33].volume = 0.67

    tw.prolong(46, F(1, 32), cello)
    tw.crop(47, cello, F(3, 8))
    cello[48].pitch = [ji.r(72, 49).register(-1)]
    cello[48].volume = 0.6
    cello[48].string_contact_point = ARCO
    cello[49].optional = None
    cello[49].volume = 0.6

    cello[52].optional = None
    cello[52].volume = 0.65

    cello[55].acciaccatura = None
    cello[55].pitch = [ji.r(7, 6).register(-1)]
    cello[55].string_contact_point = PIZZ
    cello[55].volume = 1.5
    tw.prolong(55, F(1, 32) + F(3, 8), cello)

    tw.rest(54, cello)
    tw.rest(52, cello)
    tw.rest(51, cello)

    tw.rest_many(tuple(range(64, 73)), cello)
    tw.rest(65, cello)

    tw.crop(64, cello, F(4, 4), F(2, 4), F(3, 4))
    for n, p in (
        (64, ji.r(7, 6).register(-1)),
        (65, ji.r(3, 7)),
        (66, ji.r(72, 49).register(-1)),
    ):
        cello[n].pitch = [p]
        cello[n].volume = 0.45
        cello[n].string_contact_point = ARCO

    tw.crop(40, cello, F(3, 8), F(1, 8))
    cello[41].pitch = [ji.r(6, 7)]
    cello[42].pitch = [ji.r(7, 12)]

    for n in (41, 42):
        cello[n].volume = 0.4
        cello[n].string_contact_point = ARCO

    tw.swap_duration(55, 54, F(1, 8), cello)
    tw.crop(54, cello, *([F(1, 8)] * 6))
    cello[54].pitch = [ji.r(7, 6)]
    cello[55].pitch = [ji.r(72, 49).register(-1)]
    cello[56].pitch = [ji.r(384, 245).register(-1)]
    cello[57].pitch = [ji.r(6, 7).register(-1)]
    cello[58].pitch = []
    cello[59].pitch = [ji.r(7, 12)]
    cello[60].pitch = [ji.r(1, 1)]

    tw.eat(57, 58, cello)

    tw.crop(53, cello, F(1, 16) + F(2, 16), F(2, 16), F(3, 16), F(1, 16))
    cello[54].pitch = [ji.r(72, 49).register(-1)]
    cello[55].pitch = [ji.r(72, 49).register(-2)]
    cello[56].pitch = [ji.r(72, 49).register(-1)]

    for n in (54, 55, 56):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.3

    tw.prolong(62, F(1, 8), cello)
    tw.crop(63, cello, F(1, 8), F(1, 8) + F(3, 16))

    cello[64].pitch = [ji.r(3, 7)]
    cello[64].string_contact_point = ARCO
    cello[64].volume = 0.2

    cello[65].pitch = [ji.r(6, 7)]
    cello[65].volume = 1.3
    # cello[65].volume = 0.3
    cello[65].string_contact_point = PIZZ
    # cello[65].string_contact_point = ARCO

    tw.rest(66, cello)

    # tw.swap_duration(66, 65, F(1, 16), cello)
    tw.prolong(65, F(4, 16), cello)
    tw.swap_duration(65, 64, F(1, 16), cello)

    tw.crop(64, cello, F(1, 8), position=False)
    cello[65].pitch = [ji.r(1, 2)]
    cello[66].pitch = [ji.r(7, 12)]
    tw.crop(66, cello, F(1, 8))
    cello[67].pitch = [ji.r(1, 2)]

    tw.rest_many((69, 70, 71, 72, 73, 74, 75, 76, 77), cello)

    tw.prolong(67, F(2, 4), cello)
    tw.crop(67, cello, F(1, 8))
    cello[68].pitch = [ji.r(7, 24)]

    tw.postpone(66, F(1, 16), cello)

    cello[66].pitch = [ji.r(3, 7)]
    cello[66].string_contact_point = PIZZ
    cello[66].volume = 1.3

    tw.swap_duration(64, 65, F(1, 8), cello)

    tw.crop(70, cello, F(3, 4))
    cello[71].pitch = [ji.r(8, 15)]
    cello[71].string_contact_point = ARCO
    cello[71].volume = 0.4

    tw.crop(71, cello, F(3, 8))
    cello[71].string_contact_point = PIZZ
    cello[71].volume = 1.3

    tw.change_octave(73, -1, cello)

    cello[72].string_contact_point = PIZZ
    cello[72].volume = 1.3

    cello[73].string_contact_point = PIZZ
    cello[73].volume = 1.3

    tw.crop(72, cello, F(1, 8), F(1, 8))
    cello[72].pitch = [ji.r(16, 15).register(-1)]
    cello[74].pitch = [ji.r(12, 7).register(-1)]
    cello[75].pitch = [ji.r(72, 49).register(-1)]
    tw.rest(73, cello)

    tw.crop(75, cello, F(1, 4), F(1, 4), F(1, 8), F(1, 8), F(1, 4))
    tw.change_octave(76, -1, cello)
    tw.change_octave(78, -1, cello)
    cello[79].pitch = [ji.r(6, 7)]

    cello[80].pitch = [ji.r(1, 1)]
    # tw.rest(80, cello)

    # cello[76].string_contact_point = ARCO
    # cello[76].volume = 0.3

    # tw.postpone(80, F(1, 4), cello)
    tw.crop(80, cello, F(1, 4))
    cello[80].string_contact_point = PIZZ
    cello[80].volume = 1.3
    tw.change_octave(80, -1, cello)

    tw.crop(82, cello, F(1, 4))
    cello[82].string_contact_point = PIZZ
    cello[82].volume = 1.3
    tw.change_octave(82, -1, cello)

    tw.crop(83, cello, F(1, 4), F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    tw.rest(84, cello)

    cello[85].pitch = [ji.r(6, 7)]
    cello[86].pitch = [ji.r(7, 6)]
    cello[87].pitch = [ji.r(16, 15)]
    cello[88].pitch = [ji.r(7, 12)]

    for n in (85, 86, 87, 88):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.3

    # tw.crop(88, cello, F(1, 4))
    # cello[89].pitch = [ji.r(7, 12)]
    # cello[89].string_contact_point = ARCO
    # cello[89].volume = 0.7


def _adapt_keyboard_right(right: lily.NOventLine, vm) -> None:
    right[6].optional_some_pitches = None
    tw.crop(6, right, F(3, 8))
    right[6].pitch = [ji.r(3, 2), ji.r(2, 1)]
    right[7].pitch = [ji.r(3, 2), ji.r(7, 4)]

    right[2].pitch.append(ji.r(16, 5))
    tw.crop(3, right, F(1, 8))
    right[3].pitch = [ji.r(8, 5)]
    right[4].pitch = [ji.r(7, 4)]

    # tw.crop(17, right, F(1, 8), F(1, 2), F(1, 2), F(1, 2), F(1, 2) - F(1, 8))
    # tw.copy_pitch(16, 17, right)
    # right[18].pitch = [ji.r(3, 2)]
    # right[19].pitch = [ji.r(35, 24)]
    # right[20].pitch = [ji.r(7, 9)]
    # right[21].pitch = [ji.r(35, 24)]

    right[22].optional_some_pitches = None
    tw.rest(27, right)

    tw.crop(26, right, F(3, 4), F(4, 4), F(2, 4))
    for n, r in ((26, (35 * 2, 32)), (27, (16, 15)), (28, (384, 245 * 2))):
        right[n].pitch = [ji.r(*r)]
        right[n].volume = 0.4

    tw.swap_duration(29, 30, F(1, 4), right)
    tw.change_octave(30, -2, right)

    tw.swap_duration(18, 17, F(1, 8), right)
    tw.crop(24, right, F(2, 4))
    right[25].pitch.append(ji.r(6, 7))

    tw.crop(36, right, F(1, 4))
    tw.rest(37, right)

    tw.shorten(23, F(1, 8), right)
    right[24].pitch = [ji.r(8, 7), ji.r(48, 35).register(1)]

    tw.rest_many(tuple(range(48, 53)), right)
    tw.rest(49, right)

    tw.crop(48, right, F(1, 8), F(4, 4), F(2, 4), F(3, 4))
    for n, p in (
        (49, ji.r(35, 24)),
        (50, ji.r(3, 4)),
        (51, ji.r(72, 49).register(-1)),
    ):
        right[n].pitch = [p]
        right[n].volume = 0.8

    tw.change_octave(27, -2, right)
    tw.rest(27, right)

    tw.rest(39, right)
    tw.shorten(39, F(3, 32), right)
    right[40].pitch = [ji.r(8, 7), ji.r(8, 5)]
    right[40].volume = 0.7

    tw.rest(41, right)

    tw.prolong(40, F(1, 16), right)

    tw.crop(38, right, F(1, 4), position=False)
    right[39].pitch = [ji.r(2, 3)]

    tw.eat(44, 43, right)
    tw.prolong(43, F(1, 32), right)
    tw.prolong(43, F(3, 16), right)

    right[44].optional_some_pitches = None
    tw.prolong(45, F(1, 8), right)

    tw.rest_many((45, 46), right)

    right[46].pitch = [ji.r(7, 12)]
    right[48].pitch = [ji.r(35, 24)]
    tw.crop(48, right, F(3, 8))
    right[49].pitch = []

    tw.crop(47, right, F(2, 4), F(1, 4))
    right[48].pitch = [ji.r(3, 4)]

    tw.swap_duration(32, 31, F(1, 8), right)
    tw.crop(32, right, F(1, 8))
    right[32].pitch = [ji.r(7, 12)]
    tw.rest(5, right)


def _adapt_keyboard_left(left: lily.NOventLine, vm) -> None:
    tw.swap_duration(0, 1, F(1, 32), left)
    left[1].pitch = [ji.r(35, 32).register(-2)]
    left[2].pitch = [ji.r(144, 245), ji.r(48, 49).register(-2)]
    left[6].pitch = [ji.r(7, 8)]
    left[8].pitch = [ji.r(7, 8)]
    left[9].pitch = [ji.r(7, 6)]

    left[8].optional = None
    tw.crop(10, left, F(1, 4), F(1, 4))

    for n, pitch, in ((10, ji.r(3, 2)), (11, ji.r(35, 24))):
        tw.add_kenong(n, left, pitch)
        left[n].volume = 1

    tw.crop(9, left, F(1, 16))
    left[10].pitch = [ji.r(7, 8)]

    tw.crop(14, left, F(1, 8))
    left[15].pitch = [ji.r(7, 8)]
    left[19].pitch = [ji.r(4, 3)]
    left[20].articulation_once = None
    tw.swap_duration(19, 20, F(1, 32), left)
    left[21].pitch = [ji.r(7, 9)]

    tw.add_kenong(18, left, ji.r(3, 2))

    left[26].pitch = [ji.r(7, 6)]

    tw.crop(27, left, F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    for n, pitch, in (
        (27, ji.r(3, 2)),
        (28, ji.r(35, 24)),
        (29, ji.r(14, 9)),
        (30, ji.r(35, 24)),
    ):
        if n == 27:
            tw.add_gong(n, left, pitch)
        else:
            tw.add_kenong(n, left, pitch)

        left[n].volume = 1

    left[31].ottava = attachments.Ottava(0)

    # tw.eat(10, 9, left)
    # left[8].pitch = [ji.r(1, 1)]
    left[10].pitch = [ji.r(4, 5)]
    tw.add_kenong(9, left, ji.r(3, 2))
    tw.rest(11, left)
    tw.swap_duration(11, 12, F(1, 8), left)
    # left[9].laissez_vibrer = attachments.LaissezVibrer()

    tw.rest_many(tuple(range(43, 51)), left)

    tw.crop(42, left, F(3, 4))
    tw.crop(43, left, *([F(1, 4)] * 9))
    current_idx = 43
    for n, pitch in ((3, ji.r(35, 32)), (4, ji.r(16, 15)), (2, ji.r(256, 245))):
        is_first = True
        for _ in range(n):
            if is_first:
                tw.add_gong(current_idx, left, pitch)
                is_first = False
            else:
                tw.add_kenong(current_idx, left, pitch)
                left[current_idx].volume = 1

            current_idx += 1

    tw.crop(31, left, F(3, 8), F(1, 8))
    tw.add_kenong(32, left, ji.r(3, 2))

    left[38].optional_some_pitches = None

    tw.crop(34, left, F(1, 8))
    [tw.crop(n, left, F(1, 16)) for n in (36, 35, 34)]
    tw.add_kenong(34, left, ji.r(16, 15))
    left[34].ottava = attachments.Ottava(0)
    left[34].pitch.append(ji.r(48, 35).register(-2))
    left[35].pitch = [ji.r(8, 15)]
    left[36].pitch = [ji.r(4, 5)]
    left[37].pitch = [ji.r(8, 15)]
    left[38].pitch = [ji.r(48, 35).register(-2)]
    left[39].pitch = [ji.r(8, 15)]

    tw.rest(33, left)
    left[33].ottava = attachments.Ottava(0)
    tw.rest(40, left)
    tw.rest(39, left)
    tw.rest(38, left)

    left[38].volume = 0.7
    tw.crop(38, left, F(1, 8), F(1, 16), F(1, 16))
    left[41].volume = 0.7
    left[41].ottava = attachments.Ottava(0)
    tw.crop(41, left, F(1, 16), F(1, 16))
    tw.add_kenong(39, left, ji.r(35, 32))
    left[39].ottava = attachments.Ottava(0)
    left[39].pitch.append(ji.r(35, 32).register(-2))
    left[40].pitch = [ji.r(7, 6).register(-2)]
    left[41].pitch = [ji.r(35, 24).register(-1)]
    left[42].pitch = [ji.r(7, 6).register(-2)]
    tw.rest(43, left)

    left[44].pitch.append(ji.r(7, 6))
    left[44].pitch.append(ji.r(35, 32))

    tw.crop(59, left, F(2, 4))
    # tw.add_kenong(60, left, ji.r(35, 32))
    # left[60].volume = 0.6
    left[60].volume = 0.7
    left[60].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    left[60].ottava = attachments.Ottava(0)
    left[60].pitch = [ji.r(35, 32), ji.r(35, 24), ji.r(7, 6), ji.r(4, 3), ji.r(7, 8)]

    left[61].optional_some_pitches = None
    left[61].arpeggio = None
    tw.crop(61, left, F(3, 8), F(1, 8))

    # tw.copy_pitch(60, 62, left)
    left[62].pitch = [ji.r(48, 49).register(-2)]
    left[63].pitch = [ji.r(72, 49), ji.r(288, 245)]
    left[62].volume = 0.6
    left[63].volume = 0.6
    tw.eat(63, 64, left)
    tw.rest(64, left)

    tw.crop(65, left, F(1, 8))
    left[66].pitch = [ji.r(384, 245), ji.r(288, 245)]

    for n in (65, 66):
        left[n].articulation_once = attachments.ArticulationOnce(".")

    # tw.swap_duration(67, 68, F(1, 16), left)
    tw.swap_duration(70, 69, F(1, 16), left)
    tw.swap_duration(72, 71, F(1, 16), left)

    for n in range(67, 69 + 4):
        left[n].volume = 0.78
        # left[n].articulation_once = attachments.ArticulationOnce(".")
        left[n].arpeggio = None
        if n % 2 == 0:
            tw.copy_pitch(66, n, left)
        else:
            tw.copy_pitch(63, n, left)

    left[71].articulation_once = None
    tw.eat(71, 72, left)

    left[68].articulation_once = None
    left[68].pitch = list(sorted(left[68].pitch)[1:])

    tw.rest_many((71, 70, 69), left)
    tw.crop(69, left, *([F(1, 16)] * 8))

    # siter cengkok pdf page 12 clempungan book
    for n, p in zip(
        tuple(range(69, 69 + 8)),
        (
            ji.r(288, 245).register(0),
            ji.r(35, 32).register(0),
            ji.r(288, 245).register(-1),
            ji.r(384, 245).register(-2),
            ji.r(48, 49).register(-2),
            ji.r(288, 245).register(-1),
            ji.r(35, 32).register(0),
            ji.r(288, 245).register(0),
        ),
    ):
        left[n].pitch = [p]
        left[n].volume = 0.76

    tw.swap_duration(74, 73, F(1, 32), left)

    tw.rest_many((45, 46, 47, 48), left)

    tw.crop(45, left, F(2, 32), F(2, 32), F(2, 32), F(2, 32))

    left[45].pitch = [ji.r(35, 32).register(-2)]
    left[46].pitch = [ji.r(7, 6).register(-2)]
    left[47].pitch = [ji.r(35, 24).register(-1)]
    left[48].pitch = [ji.r(7, 6).register(-2)]

    for n in range(45, 49):
        left[n].volume = 0.68

    tw.crop(49, left, F(3, 4), F(1, 4), F(2, 4))
    tw.add_gong(50, left, ji.r(8, 7))
    tw.add_kenong(51, left, ji.r(8, 7))

    left[50].volume = 1
    left[51].volume = 1

    tw.crop(49, left, F(3, 8), F(3, 8))
    tw.add_kenong(50, left, ji.r(8, 7))
    left[50].volume = 1.2

    tw.crop(54, left, F(1, 8))
    tw.swap_duration(56, 55, F(1, 8), left)

    tw.add_gong(55, left, ji.r(35, 24))

    # tw.eat(58, 59, left)
    tw.add_gong(59, left, ji.r(8, 5))

    """
    tw.crop(53, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    left[53].pitch.append(ji.r(35, 32).register(-2))
    left[54].pitch = [ji.r(7, 4).register(-1)]
    left[55].pitch = [ji.r(35, 24).register(-1)]
    left[56].pitch = [ji.r(7, 4).register(-1)]

    tw.rest(58, left)
    left[58].volume = 0.67
    tw.crop(58, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    left[58].pitch = [ji.r(35, 32).register(-2)]
    left[59].pitch = [ji.r(7, 6).register(-2)]
    left[60].pitch = [ji.r(35, 24).register(-1)]
    left[61].pitch = [ji.r(7, 6).register(-2)]

    for n in (54, 55, 56, 58, 59, 60, 61):
        left[n].ottava = attachments.Ottava(0)
        left[n].pedal = attachments.Pedal(False)
    """

    tw.rest_many(tuple(range(98, 112)), left)

    tw.crop(98, left, *([F(1, 4)] * 9))
    current_idx = 98
    for n, pitch in ((4, ji.r(35, 24)), (2, ji.r(3, 2)), (3, ji.r(72, 49))):
        is_first = True
        for _ in range(n):
            if is_first:
                tw.add_gong(current_idx, left, pitch)
                is_first = False
            else:
                tw.add_kenong(current_idx, left, pitch)
                left[current_idx].volume = 1

            current_idx += 1

    """
    tw.crop(53, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    left[53].pitch.append(ji.r(35, 32).register(-2))
    left[54].pitch = [ji.r(7, 4).register(-1)]
    left[55].pitch = [ji.r(35, 24).register(-1)]
    left[56].pitch = [ji.r(7, 4).register(-1)]

    tw.rest(58, left)
    left[58].volume = 0.67
    tw.crop(58, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    left[58].pitch = [ji.r(35, 32).register(-2)]
    left[59].pitch = [ji.r(7, 6).register(-2)]
    left[60].pitch = [ji.r(35, 24).register(-1)]
    left[61].pitch = [ji.r(7, 6).register(-2)]

    left[57].volume = 0.67
    tw.crop(57, left, F(1, 16), F(1, 16))
    left[57].pitch = [ji.r(35, 32)]
    left[58].pitch = [ji.r(7, 4).register(-1)]

    for n in (54, 55, 56, 58):
        left[n].ottava = attachments.Ottava(0)
        left[n].pedal = attachments.Pedal(False)

    """

    tw.eat(51, 52, left)

    tw.swap_duration(49, 45, F(1, 16), left)
    # for n in (48, 47, 46, 45):
    #     tw.swap_duration(49, n, F(1, 16), left)

    tw.crop(80, left, F(1, 8))
    left[81].pedal = attachments.Pedal(False)
    left[81].ottava = attachments.Ottava(0)
    left[81].volume = 0.76
    tw.crop(81, left, *([F(1, 8)] * 5))

    left[80].pitch.append(ji.r(35, 24).register(-1))
    left[81].pitch = [ji.r(48, 49).register(-2)]
    left[82].pitch = [ji.r(384, 245).register(-2)]
    left[83].pitch = [ji.r(8, 7).register(-1)]
    left[84].pitch = [ji.r(35, 24).register(-1)]
    left[85].pitch = [ji.r(7, 4).register(-1)]

    tw.swap_duration(84, 83, F(1, 16), left)

    tw.add_gong(86, left, ji.r(8, 5))
    left[86].volume = 0.67
    left[86].arpeggio = None
    # left[86].pitch.append(ji.r(8, 5).register(-1))

    tw.rest_many((87, 88, 89, 90, 91, 92), left)

    tw.crop(87, left, F(2, 4))
    left[87].pitch = [
        ji.r(4, 7).register(keyboard.SYMBOLIC_GONG_OCTAVE),
        ji.r(4, 5).register(keyboard.SYMBOLIC_GONG_OCTAVE),
    ]
    left[87].volume = 0.89
    # left[87].articulation_once = attachments.ArticulationOnce(".")
    left[87].pedal = attachments.Pedal(False)
    left[87].ottava = attachments.Ottava(-1)
    left[87].volume = 0.89
    tw.swap_duration(86, 87, F(1, 8), left)
    # tw.crop(87, left, F(1, 8), F(1, 8), F(1, 8), F(2, 16), F(2, 16))
    tw.crop(87, left, F(1, 4), F(1, 4), F(1, 8))

    left[89].pitch = [
        ji.r(14, 9).register(keyboard.SYMBOLIC_GONG_OCTAVE),
        ji.r(1, 1).register(keyboard.SYMBOLIC_GONG_OCTAVE),
    ]

    tw.crop(90, left, F(1, 4))
    tw.add_gong(90, left, ji.r(14, 9))

    # tw.rest(87, left)

    tw.crop(50, left, F(1, 4), F(1, 8))
    tw.crop(52, left, F(1, 8), F(1, 4), F(1, 4), F(1, 8))

    for n in (51, 53, 54, 55):
        if n in (51, 53):
            p0, p1, p2 = ji.r(72, 49), ji.r(8, 7), None
        elif n == 54:
            p0, p1, p2 = ji.r(8, 7), None, None
        else:
            p0, p1, p2 = ji.r(7, 6), None, ji.r(14, 9)

        tw.add_kenong(n, left, p0)
        if p1:
            left[n].pitch.append(p1.register(keyboard.SYMBOLIC_GONG_OCTAVE))
        if p2:
            left[n].pitch.append(p2.register(keyboard.SYMBOLIC_GONG_OCTAVE))
        left[n].volume = 1.1

    tw.rest(55, left)

    tw.eat(51, 52, left)
    # tw.eat(61, 62, left)
    tw.prolong(93, F(2, 4), left)
    tw.postpone(93, F(1, 4), left)
    left[94].volume = 1.2

    left[97].optional = None
    left[98].optional_some_pitches = None

    tw.rest_many(tuple(range(100, 104)), left)
    tw.add_kenong(100, left, ji.r(8, 5))
    left[100].volume = 1
    tw.crop(100, left, F(1, 4), F(1, 4))

    # tw.rest(99, left)
    tw.add_kenong(101, left, ji.r(8, 7))

    tw.rest_many((102, 103, 104, 105), left)

    left[102].pitch = [ji.r(12, 7)]
    left[102].volume = 0.6
    left[102].ottava = attachments.Ottava(0)

    tw.crop(102, left, F(1, 4), F(1, 4), F(1, 8), F(1, 8), F(3, 16), F(1, 16))
    left[103].pitch = [ji.r(72, 49)]
    left[105].pitch = [ji.r(72, 49)]
    left[107].pitch = [ji.r(3, 4)]

    tw.add_gong(108, left, ji.r(1, 1))
    tw.add_kenong(109, left, ji.r(7, 6))

    # tw.eat(111, 112, left)
    tw.add_kenong(112, left, ji.r(3, 2))
    left[112].volume = 1.2


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        "opening",
        tempo_factor=0.283,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.15,
        ro_temperature=0.67,
        ro_density=0.7,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.2, 0.01),
        area_density_reference_size=F(1, 4),
        area_min_split_size=F(1, 8),
    )

    vm.remove_area(0, 2)
    vm.remove_area(15, 17)
    vm.remove_area(29, len(vm.bars))
    vm.repeat_area(5, 9)

    vm.verse = "opening"

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(4, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(5),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(2),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.59,
            harmonic_pitches_density=0.65,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            after_glissando_size=F(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(1),
            pizz_maker=infit.ActivityLevel(3, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(7),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(5),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.56,
            harmonic_pitches_density=0.62,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_density=0.5,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(0),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2, 0, 1, 0)),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(9),
            harmonic_pitches_activity=0.57,
            harmonic_pitches_density=0.65,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(1, 8),
            optional_pitches_density=0.6,
        ),
        keyboard=keyboard.KeyboardMaker(
            lh_min_metricity_to_add_accent=1.5, colotomic_structure=(1, 2, 0, 2)
        ),
    )

    #############################################################################
    #                           TWEAKS / post processing                        #
    #############################################################################

    ################################
    #          VIOLIN              #
    ################################

    # tw.shorten(2, F(1, 8), vm.violin.musdat[1])
    tw.add_glissando(2, (0, 0, -1), vm.violin.musdat[1], verse_maker=vm)
    tw.swap_identity(3, 4, vm.violin.musdat[1])

    vm.violin.musdat[1][2].ornamentation = attachments.OrnamentationDown(1)

    # tw.split(
    #     8,
    #     F(1, 4),
    #     F(1, 8),
    #     F(1, 8),
    #     vm.violin.musdat[1],
    # )
    tw.prolong(5, F(1, 16), vm.violin.musdat[1])
    tw.add_glissando(
        5, (-1, 0, 0, -1), vm.violin.musdat[1], durations=(F(1, 16), F(1, 8), F(1, 8),),
    )
    tw.shorten(7, F(1, 8), vm.violin.musdat[1])
    vm.violin.musdat[1][7].acciaccatura = None
    tw.add_glissando(
        7, (2, 0, 0), vm.violin.musdat[1], durations=(F(1, 8), F(1, 4),),
    )

    tw.set_acciaccatura_pitch(11, ji.r(3, 2), vm.violin.musdat[1])

    vm.violin.musdat[1][14].tremolo = None
    vm.violin.musdat[1][14].volume = 2
    # vm.violin.musdat[1][16].prall = attachments.Prall()
    vm.violin.musdat[1][16].prall = None
    vm.violin.musdat[1][14].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    tw.rest(4, vm.violin.musdat[1])
    tw.prolong(11, F(1, 4), vm.violin.musdat[1])
    tw.split(11, vm.violin.musdat[1], F(1, 4), F(1, 8))
    tw.add_glissando(
        11, (0, 0, -1), vm.violin.musdat[1], durations=(F(1, 8), F(1, 8)),
    )
    vm.violin.musdat[1][12].pitch = [ji.r(48, 35)]
    tw.rest(18, vm.violin.musdat[1])
    tw.change_octave(18, -1, vm.violin.musdat[1], change_main_pitches=False)
    vm.violin.musdat[1][18].acciaccatura.add_glissando = True
    tw.split_by_structure(18, 4, vm.violin.musdat[1], vm)
    # making manual copies of athe acciaccatura because otherwise they will be
    # adapted by the next call.
    for n in (19, 20, 21):
        acc = vm.violin.musdat[1][n].acciaccatura
        vm.violin.musdat[1][n].acciaccatura = attachments.Acciaccatura(
            acc.mu_pitches, abjad.mutate(acc.abjad).copy(), add_glissando=False
        )
    tw.set_acciaccatura_pitch(
        18, vm.violin.musdat[1][0].pitch[0].copy(), vm.violin.musdat[1]
    )
    vm.violin.musdat[1][20].acciaccatura = None
    vm.violin.musdat[1][20].ornamentation = attachments.OrnamentationUp(1)
    vm.violin.musdat[1][23].ornamentation = attachments.OrnamentationDown(1)
    tw.add_acciaccatura(
        25,
        vm.violin.musdat[1][0].pitch[0].copy(),
        vm.violin.musdat[1],
        add_glissando=True,
    )
    tw.split_by_structure(30, 2, vm.violin.musdat[1], vm)
    vm.violin.musdat[1][31].acciaccatura = None
    tw.add_glissando(36, (0, 0, -1), vm.violin.musdat[1], verse_maker=vm)
    vm.violin.musdat[1][38].acciaccatura = None
    tw.split(
        42, vm.violin.musdat[1], F(1, 4), F(1, 4), F(3, 4),
    )
    vm.violin.musdat[1][42].pitch = [ji.r(8, 9)]
    vm.violin.musdat[1][43].pitch = [ji.r(35, 32)]
    for n in (41, 42, 43):
        vm.violin.musdat[1][n].volume = 0.4
        # vm.violin.musdat[1][n].pitch[0] += ji.r(2, 1)
        vm.violin.musdat[1][n].string_contact_point = attachments.StringContactPoint(
            "arco"
        )
        vm.violin.musdat[1][n].optional = None

    vm.violin.musdat[1][44].pitch = [ji.r(35, 32)]
    vm.violin.musdat[1][44].volume = 0.4
    vm.violin.musdat[1][44].ornamentation = attachments.OrnamentationUp(1)
    # tw.add_glissando(
    #     44,
    #     (0, 0, -1),
    #     vm.violin.musdat[1],
    #     durations=(F(5, 8), F(1, 8)),
    # )

    tw.shorten(44, F(1, 4), vm.violin.musdat[1])

    # vl_swaped_duration = F(1, 4)
    # vm.violin.musdat[1][40].delay -= vl_swaped_duration
    # vm.violin.musdat[1][40].duration -= vl_swaped_duration
    # vm.violin.musdat[1][45].delay += vl_swaped_duration
    # vm.violin.musdat[1][45].duration += vl_swaped_duration

    # tw.add_artifical_harmonic(
    #     31, vm.violin.musdat[1][31].pitch[0], vm.violin.musdat[1]
    # )
    # vm.violin.musdat[1][31].pitch[0] += ji.r(4, 1)

    ################################
    #          VIOLA               #
    ################################

    tw.swap_identity(1, 2, vm.viola.musdat[1])
    vm.viola.musdat[1][2].tremolo = None
    tw.rest(3, vm.viola.musdat[1])
    tw.prolong(2, F(1, 16), vm.viola.musdat[1])
    tw.rest(6, vm.viola.musdat[1])
    vm.viola.musdat[1][6].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.viola.musdat[1][8].acciaccatura = None
    tw.add_glissando(
        8, (-2, -2, 0), vm.viola.musdat[1], durations=(F(1, 8), F(1, 16)),
    )
    vm.viola.musdat[1][10].ornamentation = attachments.OrnamentationDown(2)
    vm.viola.musdat[1][10].acciaccatura.add_glissando = True
    vm.viola.musdat[1][12].acciaccatura.add_glissando = True
    # vm.viola.musdat[1][14].prall = attachments.Prall()
    vm.viola.musdat[1][14].prall = None

    vm.viola.musdat[1][15].pitch = [ji.r(4, 3)]
    vm.viola.musdat[1][15].volume = 0.5
    vm.viola.musdat[1][15].string_contact_point = attachments.StringContactPoint("arco")

    vm.viola.musdat[1][16].glissando = None
    # tw.swap_duration(15, 16, F(1, 8), vm.viola.musdat[1])
    # tw.split(16, F(1, 8), F(1, 8), vm.viola.musdat[1])

    tw.split_by_structure(18, 2, vm.viola.musdat[1], vm)
    vm.viola.musdat[1][19].acciaccatura = None
    vm.viola.musdat[1][19].ornamentation = attachments.OrnamentationUp(1)
    tw.add_glissando(19, (0, -1), vm.viola.musdat[1], verse_maker=vm)

    for n in (15, 16, 17, 18, 19, 21):
        tw.change_octave(n, -1, vm.viola.musdat[1])

    # tw.add_glissando(23, (0, -2), vm.viola.musdat[1], verse_maker=vm)
    tw.rest(23, vm.viola.musdat[1])
    vm.viola.musdat[1][25].acciaccatura = None
    vm.viola.musdat[1][25].optional = None
    vm.viola.musdat[1][25].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.viola.musdat[1][30].acciaccatura = None
    vm.viola.musdat[1][32].string_contact_point = attachments.StringContactPoint("arco")
    vm.viola.musdat[1][32].optional = None
    vm.viola.musdat[1][32].volume = 0.7
    vm.viola.musdat[1][32].pitch[0] -= ji.r(2, 1)
    tw.prolong(32, F(7, 32), vm.viola.musdat[1])

    vm.viola.musdat[1][33].pitch[0] -= ji.r(2, 1)
    vm.viola.musdat[1][33].volume = 0.7
    tw.add_acciaccatura(
        35,
        globals_.SCALE_PER_INSTRUMENT["viola"][0].register(-1),
        vm.viola.musdat[1],
        add_glissando=True,
    )
    vm.viola.musdat[1][36].ornamentation = attachments.OrnamentationUp(1)
    vm.viola.musdat[1][38].glissando = None
    vm.viola.musdat[1][39].acciaccatura = None
    tw.split_by_structure(39, 3, vm.viola.musdat[1], verse_maker=vm)
    tw.rest(41, vm.viola.musdat[1])

    vm.viola.musdat[1][-1].pitch = [ji.r(35, 48)]
    vm.viola.musdat[1][-1].volume = 0.4
    tw.shorten(51, F(1, 4), vm.viola.musdat[1])
    vm.viola.musdat[1][-3].hauptstimme = attachments.Hauptstimme(True, False)
    vm.viola.musdat[1][-2].hauptstimme = attachments.Hauptstimme(False, False)

    # tw.add_glissando(
    #     -1,
    #     (0, 0, -1),
    #     vm.viola.musdat[1],
    #     durations=(F(5, 8), F(1, 8)),
    # )

    # tw.add_artifical_harmonic(
    #     33, vm.viola.musdat[1][33].pitch[0] - ji.r(2, 1), vm.viola.musdat[1]
    # )
    # vm.viola.musdat[1][33].pitch[0] += ji.r(2, 1)

    ################################
    #          CELLO               #
    ################################
    vm.cello.musdat[1][1].optional = None
    tw.prolong(1, F(1, 8), vm.cello.musdat[1])
    tw.rest(2, vm.cello.musdat[1])
    vm.cello.musdat[1][3].acciaccatura = None
    vm.cello.musdat[1][3].optional = None
    vm.cello.musdat[1][3].pitch[0] += ji.r(2, 1)
    tw.rest(5, vm.cello.musdat[1])

    tw.prolong(5, F(1, 8), vm.cello.musdat[1])
    vm.cello.musdat[1][5].optional = None
    vm.cello.musdat[1][5].acciaccatura = None
    vm.cello.musdat[1][5].pitch[0] += ji.r(2, 1)
    tw.add_glissando(5, (0, 0, -1), vm.cello.musdat[1], verse_maker=vm)
    vm.cello.musdat[1][7].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.cello.musdat[1][9].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    tw.split_by_structure(9, 3, vm.cello.musdat[1], vm)
    vm.cello.musdat[1][11].bartok_pizzicato = attachments.BartokPizzicato()

    tw.rest(13, vm.cello.musdat[1])

    vm.cello.musdat[1][13].acciaccatura = None
    vm.cello.musdat[1][13].pitch = [ji.r(16, 15).register(-1)]
    vm.cello.musdat[1][14].acciaccatura.add_glissando = False

    for n in (13, 14, 15, 16):
        # vm.cello.musdat[1][n].string_contact_point = attachments.StringContactPoint(
        #     "pizzicato"
        # )
        tw.change_octave(n, -1, vm.cello.musdat[1])

    for n in (20, 19, 18):
        tw.rest(n, vm.cello.musdat[1])

    tw.shorten(21, F(1, 16), vm.cello.musdat[1])

    for n, acc_pitch in zip(
        (18, 19, 21, 23, 24, 25, 26), itertools.cycle((ji.r(7, 8), ji.r(7, 12)))
    ):
        vm.cello.musdat[1][n].string_contact_point = attachments.StringContactPoint(
            "pizzicato"
        )
        if vm.cello.musdat[1][n].acciaccatura:
            if n == 26:
                vm.cello.musdat[1][n].acciaccatura = None
            elif n == 25:
                vm.cello.musdat[1][n].acciaccatura = None
                vm.cello.musdat[1][n].natural_harmonic = attachments.NaturalHarmonic()
                tw.change_octave(n, -1, vm.cello.musdat[1])
            else:
                tw.set_acciaccatura_pitch(n, acc_pitch, vm.cello.musdat[1])
                tw.change_octave(
                    n, -2, vm.cello.musdat[1], change_acciaccatura_pitches=False
                )
                vm.cello.musdat[1][n].acciaccatura.add_glissando = False

    tw.swap_duration(28, 29, F(1, 16), vm.cello.musdat[1])
    vm.cello.musdat[1][29].acciaccatura = None
    vm.cello.musdat[1][29].optional = None
    tw.rest(31, vm.cello.musdat[1])

    for n in (31, 36):
        vm.cello.musdat[1][n].choose = None
        vm.cello.musdat[1][n].pitch = vm.cello.musdat[1][n].pitch[:1]

    vm.cello.musdat[1][33].acciaccatura = None
    vm.cello.musdat[1][34].acciaccatura = None
    vm.cello.musdat[1][38].acciaccatura = None

    tw.rest(34, vm.cello.musdat[1])
    tw.prolong(33, F(3, 16), vm.cello.musdat[1])
    tw.swap_duration(32, 33, F(5, 32), vm.cello.musdat[1])
    tw.add_glissando(
        32, (-1, 0, 0), vm.cello.musdat[1], durations=(F(5, 32), F(5, 16)),
    )

    tw.swap_duration(19, 18, F(3, 16), vm.cello.musdat[1])
    vm.cello.musdat[1][18].acciaccatura = None
    vm.cello.musdat[1][18].natural_harmonic = attachments.NaturalHarmonic()
    vm.cello.musdat[1][18].string_contact_point = attachments.StringContactPoint("arco")
    vm.cello.musdat[1][18].pitch[0] += ji.r(2, 1)
    vm.cello.musdat[1][18].acciaccatura = None

    vm.cello.musdat[1][38].volume = 0.67
    tw.change_octave(38, 1, vm.cello.musdat[1], change_acciaccatura_pitches=False)
    tw.change_octave(39, 1, vm.cello.musdat[1], change_acciaccatura_pitches=False)
    vm.cello.musdat[1][38].optional = None  # TODO(really?)
    vm.cello.musdat[1][38].acciaccatura = None
    vm.cello.musdat[1][39].optional = None  # TODO(really?)
    vm.cello.musdat[1][39].acciaccatura = None
    vm.cello.musdat[1][39].volume = 0.7
    vm.cello.musdat[1][39].natural_harmonic = attachments.NaturalHarmonic()
    tw.prolong(39, F(9, 32), vm.cello.musdat[1])
    tw.swap_duration(40, 39, F(3, 16), vm.cello.musdat[1])

    for n in (41, 43, 44):
        tw.change_octave(n, -1, vm.cello.musdat[1], change_acciaccatura_pitches=False)
        vm.cello.musdat[1][n].string_contact_point = attachments.StringContactPoint(
            "pizzicato"
        )
        vm.cello.musdat[1][n].acciaccatura.add_glissando = False

    tw.rest(45, vm.cello.musdat[1])
    tw.swap_duration(54, 53, F(5, 32), vm.cello.musdat[1])

    vm.cello.musdat[1][49].optional = None

    for n in (46, 47, 48, 49, 51, 52, 53):
        tw.change_octave(n, 1, vm.cello.musdat[1])

    for n in (55, 56, 57):
        vm.cello.musdat[1][n].acciaccatura = None
        tw.change_octave(n, 1, vm.cello.musdat[1])

    tw.split(58, vm.cello.musdat[1], F(1, 8), F(3, 4))
    # vm.cello.musdat[1][-1].pitch = [ji.r(7, 12)]

    # CS = F(7, 4)
    # print(vm.cello.musdat[1].convert2absolute()[18])
    # ev = vm.cello.musdat[1].convert2absolute()[18]
    # for slice_ in vm.bread.find_responsible_slices(CS + ev.delay, CS + ev.duration + 2):
    #     print(slice_.melody_pitch)
    #     print(slice_.harmonic_pitch)
    #     print(slice_.harmonic_field)
    #     print("")

    ################################
    #          keyboard            #
    ################################

    # right hand
    vm.keyboard.musdat[1][13].pitch[0] = vm.keyboard.musdat[1][2].pitch[0].copy()

    # left hand
    vm.keyboard.musdat[2][1].optional = None
    vm.keyboard.musdat[2][22].articulation = attachments.ArticulationOnce(".")
    vm.keyboard.musdat[2][23].arpeggio = None
    vm.keyboard.musdat[2][23].ottava = attachments.Ottava(-1)
    vm.keyboard.musdat[2][23].pitch = list(sorted(vm.keyboard.musdat[2][21].pitch)[:1])
    vm.keyboard.musdat[2][33].articulation_once = None
    # vm.keyboard.musdat[2][31].pitch = [vm.keyboard.musdat[2][30].pitch[0].copy()]
    tw.shorten(48, F(3, 4), vm.keyboard.musdat[2])
    vm.keyboard.musdat[2][48].articulation_once = None
    tw.swap_duration(33, 32, F(1, 8), vm.keyboard.musdat[2])
    # for n in (37, 36, 35, 34, 33, 32, 31, 28, 27):
    for n in (40, 39, 38, 37, 36, 35, 34, 31, 30):
        if n == 34:
            tw.swap_duration(34, 33, F(1, 4), vm.keyboard.musdat[2])
        else:
            tw.rest(n, vm.keyboard.musdat[2])
        # tw.rest(n, vm.keyboard.musdat[2])

    vm.keyboard.musdat[2].append(type(vm.keyboard.musdat[2][0])())
    keyboard_swap_dur_size = F(3, 4)
    vm.keyboard.musdat[2][-2].duration -= keyboard_swap_dur_size
    vm.keyboard.musdat[2][-2].delay -= keyboard_swap_dur_size
    vm.keyboard.musdat[2][-1].duration = keyboard_swap_dur_size
    vm.keyboard.musdat[2][-1].delay = keyboard_swap_dur_size
    vm.keyboard.musdat[2][-1].pitch = [
        ji.r(35, 24).register(keyboard.SYMBOLIC_GONG_OCTAVE)
    ]
    vm.keyboard.musdat[2][-1].ottava = attachments.Ottava(-1)
    vm.keyboard.musdat[2][-1].pedal = attachments.Pedal(True)
    vm.keyboard.musdat[2][-3].optional = None

    ###################################
    #  second round of postprocessing #
    ###################################

    vm.add_bar(2, abjad.TimeSignature((2, 4)))
    vm.add_bar(7, abjad.TimeSignature((4, 4)))
    vm.add_bar(7, abjad.TimeSignature((4, 4)))
    vm.add_bar(9, abjad.TimeSignature((2, 4)))
    vm.add_bar(17, abjad.TimeSignature((3, 4)))
    # vm.add_bar(24, abjad.TimeSignature((3, 4)))

    _adapt_violin(vm.violin.musdat[1], vm)
    _adapt_viola(vm.viola.musdat[1], vm)
    _adapt_cello(vm.cello.musdat[1], vm)
    _adapt_keyboard_right(vm.keyboard.musdat[1], vm)
    _adapt_keyboard_left(vm.keyboard.musdat[2], vm)

    vm.add_bar(0, abjad.TimeSignature((2, 4)))
    vm.add_bar(2, abjad.TimeSignature((3, 4)))
    vm.add_bar(32, abjad.TimeSignature((4, 4)), force_adding=True)

    _add_vl_intro(vm.violin.musdat[1], vm)
    _add_va_intro(vm.viola.musdat[1], vm)
    _add_vc_intro(vm.cello.musdat[1], vm)
    _add_left_intro(vm.keyboard.musdat[2], vm)

    ################################
    #  changes for all instrument  #
    ################################

    for string in (vm.violin.musdat[1], vm.viola.musdat[1], vm.cello.musdat[1]):
        tw.detach_hauptstimme(string)

    for instr in (
        vm.violin.musdat[1],
        vm.viola.musdat[1],
        vm.cello.musdat[1],
        vm.keyboard.musdat[2],
        vm.keyboard.musdat[1],
    ):
        tw.detach_optional_events(instr)

    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            nth_line = (2, 1)
        else:
            nth_line = (1,)

        novent_line = getattr(vm, instr).musdat[nth_line[0]]
        novent_line[0].dynamic = attachments.Dynamic("pp")

    # vm.force_remove_area(1, 3)

    verse = vm()

    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            indices = ((1, 0), (1, 1))
        else:
            indices = ((1,),)

        for idx in indices:
            staff = getattr(verse, instr).abjad
            for subidx in idx:
                staff = staff[subidx]

            # [bar_idx][event_idx]
            # if type(staff[-1][-1]) == abjad.MultimeasureRest:
            #     fermata = abjad.LilyPondLiteral(
            #         "\\fermataMarkup", format_slot="absolute_after"
            #     )
            # else:
            #     fermata = abjad.Fermata()

            # abjad.attach(fermata, staff[-1][-1])

            # adapting accidental notation of keyboard
            if instr == "keyboard" and idx[1] == 0:
                # del staff[3][3]
                # staff[3].append(abjad.Note('a', F(1, 16)))
                # staff[3].append(abjad.Note('bf', F(1, 16)))
                # staff[3].append(abjad.Rest(F(1, 16)))
                # staff[3].append(abjad.Note('g', F(1, 16)))
                # abjad.attach(abjad.StartBeam(), staff[3][3])
                # abjad.attach(abjad.Ottava(-1), staff[3][3])
                # abjad.attach(abjad.StopBeam(), staff[3][6])
                # abjad.attach(abjad.Ottava(0), staff[4][0])

                abjad.Accidental.respell_with_sharps(staff[6][2:])
                abjad.Accidental.respell_with_sharps(staff[7])
                abjad.Accidental.respell_with_sharps(staff[8])
                abjad.Accidental.respell_with_sharps(staff[14][1:])
                abjad.Accidental.respell_with_sharps(staff[15])
                abjad.Accidental.respell_with_sharps(staff[24])
                abjad.Accidental.respell_with_sharps(staff[31])

            elif instr == "keyboard" and idx[1] == 1:
                # del staff[3][4]
                # del staff[3][5]
                # del staff[3][7]

                # staff[3].insert(4, abjad.Rest(F(1, 8)))
                # staff[3][5] = abjad.Note('g,,', F(1, 8))

                abjad.Accidental.respell_with_sharps(staff[1][3:])
                abjad.Accidental.respell_with_sharps(staff[6][3:])
                abjad.Accidental.respell_with_sharps(staff[7])
                abjad.Accidental.respell_with_sharps(staff[8])
                abjad.Accidental.respell_with_sharps(staff[14])
                abjad.Accidental.respell_with_sharps(staff[15])
                abjad.Accidental.respell_with_sharps(staff[17])
                abjad.Accidental.respell_with_sharps(staff[18])
                abjad.Accidental.respell_with_sharps(staff[19])
                abjad.Accidental.respell_with_sharps(staff[20])
                abjad.Accidental.respell_with_sharps(staff[21])
                abjad.Accidental.respell_with_sharps(staff[22])
                abjad.Accidental.respell_with_sharps(staff[23])
                abjad.Accidental.respell_with_sharps(staff[24])
                abjad.Accidental.respell_with_sharps(staff[31])
                abjad.Accidental.respell_with_sharps(staff[32])

            # lily.attach_empty_grace_note_at_beggining_of_every_bar(staff)

            if instr == "viola":
                clef = attachments.Clef("alto")
                clef.attach(staff[0], None)

            '''moved to trackmacker.strings.String
            if instr != "keyboard":
                abjad.attach(
                    abjad.Markup(
                        abjad.MarkupCommand("italic", ["con sordino, non vibrato"]),
                        direction=abjad.enums.Up,
                    ),
                    staff[0][0],
                )
            '''

    return verse
