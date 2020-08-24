import numpy as np

from quicktions import Fraction as F

import abjad

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
PIZZICATO = attachments.StringContactPoint("pizzicato")


def _adapt_violin(violin: lily.NOventLine, vm) -> None:
    tw.detach_optional_events(violin)

    violin[13].acciaccatura = None
    violin[12].acciaccatura = None
    tw.add_glissando(
        12, (0, 0, 1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )
    tw.prolong(14, F(3, 8), violin)
    tw.split(
        13, violin, F(1, 4), F(1, 8), F(1, 8),
    )
    # tw.rest(14, violin)
    # violin[14].string_contact_point = attachments.StringContactPoint('pizzicato')
    # violin[14].volume = 2
    tw.add_glissando(
        15, (0, 1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )
    violin[16].ornamentation = attachments.OrnamentationUp(2)

    tw.prolong(1, F(1, 8), violin)
    tw.change_octave(1, -1, violin)
    violin[1].acciaccatura = None
    for n in (2, 6, 8):
        violin[n].acciaccatura = None
        tw.add_glissando(
            n, (1, 0, 0, 0), violin, verse_maker=vm, adapt_by_changed_structure=True
        )

    tw.add_glissando(
        2, (-1, 0, 0, -1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )
    tw.add_glissando(
        8, (1, 0, 0, -1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )
    violin[4].string_contact_point = attachments.StringContactPoint("arco")
    tw.split(9, violin, F(1, 16), F(1, 16))
    tw.rest(9, violin)
    tw.prolong(10, F(3, 16), violin)
    tw.swap_duration(10, 9, F(1, 16), violin)
    violin[10].volume = 2.4
    tw.add_acciaccatura(17, ji.r(35, 32), violin, add_glissando=True)

    violin[25].ornamentation = attachments.OrnamentationDown(3)

    violin[36].acciaccatura = None
    tw.add_glissando(
        38, (2, 0, 0, -1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )
    violin[32].volume = 1.6
    violin[34].string_contact_point = attachments.StringContactPoint("arco")
    violin[34].volume = 0.69
    tw.swap_duration(36, 35, F(1, 8), violin)
    tw.prolong(34, F(1, 8), violin)
    tw.add_glissando(
        34, (0, 0, -1), violin, durations=[F(3, 16), F(1, 16)],
    )
    tw.add_glissando(
        36, (1, 0, 0), violin, durations=[F(1, 8), F(1, 8)],
    )

    tw.crop(0, violin, F(2, 4) + F(1, 8))
    violin[1].pitch = [ji.r(48, 35)]
    tw.set_pizz(1, violin)

    violin[6].pitch = [ji.r(7, 9)]
    tw.set_pizz(6, violin)

    # tw.crop(8, violin, F(1, 16))
    # violin[8].pitch = [ji.r(8, 9)]
    violin[10].pitch = [ji.r(7, 9)]
    tw.set_pizz(10, violin)

    tw.shorten(11, F(1, 16), violin)
    tw.crop(12, violin, F(2, 16), F(1, 16), F(1, 16))
    violin[13].pitch = [ji.r(8, 9)]
    violin[14].pitch = [ji.r(7, 9)]
    tw.set_pizz(13, violin)
    tw.set_pizz(14, violin)

    # tw.set_arco(8, violin)
    # tw.set_arco(9, violin)


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    tw.detach_optional_events(viola)

    tw.swap_duration(0, 1, F(1, 16), viola)
    tw.add_glissando(
        1, (-1, 0, 0), viola, durations=(F(1, 16), F(3, 16)),
    )
    viola[2].choose = None
    viola[2].volume = 0.5
    viola[2].pitch = viola[2].pitch[:1]
    tw.prolong(2, F(1, 32), viola)
    viola[5].pitch = [ji.r(7, 8)]
    for n in (5, 6):
        viola[n].string_contact_point = attachments.StringContactPoint("arco")
        viola[n].volume = 0.5

    # tw.change_octave(12, -1, viola)
    viola[12].pitch = [ji.r(48, 49)]
    # tw.swap_duration(11, 12, F(1, 8), viola)
    tw.prolong(12, F(5, 32), viola)
    tw.add_glissando(
        12, (-1, 0, 0), viola, durations=[F(1, 8), F(1, 4)],
    )
    # tw.split(11, viola, F(1, 8), F(1, 16))
    viola[11].pitch = [ji.r(7, 8)]
    viola[11].volume = 0.5
    viola[11].string_contact_point = attachments.StringContactPoint("arco")

    tw.change_octave(14, 1, viola)

    for n in (18, 19, 21, 22, 24):
        tw.change_octave(n, -1, viola)
        viola[n].string_contact_point = attachments.StringContactPoint("pizzicato")
        viola[n].volume = 1

    viola[25].string_contact_point = attachments.StringContactPoint("arco")
    viola[25].volume = 0.5
    tw.change_octave(25, -1, viola)

    tw.rest(24, viola)

    for n in (29, 30, 33, 35, 36, 38, 39):
        tw.change_octave(n, -1, viola)

    viola[39].string_contact_point = attachments.StringContactPoint("arco")
    viola[39].volume = 0.6

    tw.rest(31, viola)

    viola[32].acciaccatura = None
    tw.prolong(32, F(1, 32), viola)
    tw.add_glissando(
        32, (0, 0, -1), viola, durations=[F(3, 16), F(1, 16)],
    )

    viola[28].ornamentation = attachments.OrnamentationUp(2)

    tw.crop(3, viola, F(1, 4) + F(3, 16), F(1, 16), F(1, 4), F(1, 4))
    viola[4].pitch = [ji.r(35, 48)]
    viola[5].pitch = [ji.r(35, 48)]
    viola[6].pitch = [ji.r(7, 8)]
    tw.set_pizz(4, viola)
    tw.set_pizz(5, viola)
    tw.set_pizz(6, viola)
    viola[6].volume = 1.5

    tw.rest(12, viola)
    tw.prolong(10, F(1, 32), viola)
    tw.crop(11, viola, F(1, 8) + F(1, 16), F(1, 16), F(1, 8))
    viola[12].pitch = [ji.r(7, 8)]
    tw.set_pizz(12, viola)
    viola[13].pitch = [ji.r(2, 3)]
    tw.set_pizz(13, viola)

    tw.postpone(14, F(1, 8), viola)


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    tw.detach_optional_events(cello)

    cello[1].natural_harmonic = attachments.NaturalHarmonic()
    tw.change_octave(3, 1, cello, change_main_pitches=False)
    tw.change_octave(3, -2, cello, change_acciaccatura_pitches=False)
    cello[4].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[4].volume = 1
    tw.change_octave(4, 1, cello, change_main_pitches=False)
    tw.change_octave(5, -2, cello, change_acciaccatura_pitches=False)
    tw.change_octave(6, -2, cello, change_acciaccatura_pitches=False)

    cello[9].volume = 0.6
    cello[9].string_contact_point = attachments.StringContactPoint("arco")

    for n in (9, 11, 13):
        cello[n].artifical_harmonic = None
        tw.change_octave(n, -1, cello, change_acciaccatura_pitches=False)

    cello[13].glissando = None

    tw.swap_duration(10, 9, F(5, 32), cello)
    tw.swap_duration(11, 10, F(1, 16), cello)
    tw.add_glissando(
        9, (0, 0, -1), cello, durations=[F(4, 16), F(3, 32)],
    )
    tw.add_glissando(
        10, (0, 0, 1), cello, durations=[F(1, 32) + F(1, 8) + F(3, 16), F(1, 16)],
    )

    cello[14].hauptstimme = attachments.Hauptstimme(False, False)
    tw.rest(16, cello)
    tw.change_octave(16, 1, cello)
    tw.add_glissando(
        16, (0, 0, -2), cello, durations=[F(3, 16), F(1, 16)],
    )

    for n in (19, 20):
        cello[n].artifical_harmonic = None
        cello[n].acciaccatura = None
        cello[n].glissando = None
        cello[n].volume = 0.3
        tw.change_octave(n, -2, cello)

    tw.split(
        21, cello, F(7, 4) + F(1, 8), F(5, 8) + F(2, 4),
    )
    cello[21].pitch = [ji.r(7, 24)]
    cello[21].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[21].volume = 1.87
    tw.split_by_structure(21, 6, cello, vm, adapt_by_changed_structure=True)

    for n in range(21, 21 + 6):
        if n % 3 == 0:
            cello[n].pitch = [ji.r(1, 4)]

    cello[21].pitch = [ji.r(8, 15)]
    cello[22].pitch = [ji.r(1, 2)]
    for n in (21, 22, 23):
        cello[n].string_contact_point = attachments.StringContactPoint("arco")
        cello[n].volume = 0.3

    cello[23].volume = 0.6
    tw.add_acciaccatura(19, ji.r(256, 189).register(-2), cello, add_glissando=True)
    tw.add_glissando(
        21, (0, -1), cello, durations=[F(3, 16)],
    )
    tw.add_glissando(
        22, (0, 0, -1), cello, durations=[F(3, 16), F(1, 8)],
    )

    cello[6].pitch = [ji.r(7, 12)]
    cello[6].acciaccatura = None
    tw.set_arco(6, cello)

    tw.shorten(7, F(3, 32), cello)
    tw.crop(8, cello, F(3, 4), F(2, 4), F(2, 16), F(2, 16))
    cello[9].pitch = [ji.r(7, 12)]
    tw.set_pizz(9, cello)
    cello[11].pitch = [ji.r(7, 12)]
    tw.set_pizz(11, cello)

    tw.shorten(1, F(3, 32), cello)
    cello[2].pitch = [ji.r(16, 15)]
    tw.set_pizz(2, cello)

    # tw.crop(
    #  12, cello, F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8))
    tw.crop(12, cello, F(5, 4))
    cello[12].pitch = [ji.r(256, 189).register(-1)]
    tw.split_by_structure(12, 6, cello, vm, adapt_by_changed_structure=True)
    cello[13].pitch = [ji.r(7, 6).register(-1)]
    cello[14].pitch = [ji.r(1, 1).register(-1)]
    cello[15].pitch = [ji.r(7, 6).register(-1)]
    cello[16].pitch = [ji.r(72, 49).register(-1)]
    cello[17].pitch = [ji.r(384, 245).register(-1)]
    # cello[18].pitch = [ji.r(72, 49).register(-1)]

    # for n in (13, 15, 17, 19):
    for n in range(12, 19):
        cello[n].glissando = None
        cello[n].acciaccatura = None
        # tw.set_pizz(n, cello)
        # cello[n].volume = 0.6
        tw.set_arco(n, cello)
        cello[n].volume = 0.3

    # tw.set_arco(12, cello)
    # cello[12].volume = 0.3
    # tw.postpone(12, F(1, 8), cello)

    tw.add_glissando(12, (0, 0, -1), cello, durations=[F(1, 8), F(1, 8)])


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine, vm) -> None:
    tw.detach_optional_events(left)
    tw.detach_optional_events(right)

    ###################################################
    #            CHANGE RIGHT HAND                    #
    ###################################################

    _adapt_right_hand(right, vm)

    ###################################################
    #            CHANGE LEFT HAND                      #
    ###################################################

    _adapt_left_hand(left, vm)


def _adapt_right_hand(right: lily.NOventLine, vm) -> None:
    tw.swap_duration(0, 1, F(5, 16), right)
    tw.split_by_structure(17, 4, right, vm, adapt_by_changed_structure=True)
    tw.rest(19, right)
    tw.split(22, right, F(1, 8), F(3, 16))
    right[23].pitch = right[21].pitch
    right[29].optional_some_pitches = None
    right[49].optional_some_pitches = None

    tw.postpone(1, F(1, 4) + F(1, 16), right)
    tw.prolong(1, F(1, 8), right)
    tw.prolong(3, F(1, 8), right)

    right[2].pitch = [ji.r(3, 2), ji.r(2, 1)]
    right[4].pitch = [ji.r(7, 12), ji.r(35, 64)]
    right[5].pitch = [ji.r(7, 3), ji.r(14, 9), ji.r(35, 24)]
    right[6].pitch = [ji.r(7, 9), ji.r(7, 12), ji.r(1, 2)]
    right[7].pitch = [ji.r(7, 3), ji.r(35, 12), ji.r(35, 16)]
    tw.crop(7, right, F(1, 4))
    right[8].pitch = [ji.r(7, 4), ji.r(7, 3), ji.r(2, 1)]
    right[9].pitch = [ji.r(7, 3), ji.r(14, 9), ji.r(35, 24)]
    right[10].pitch = [ji.r(7, 12), ji.r(35, 64)]
    tw.prolong(10, F(1, 8), right)
    right[11].pitch = [ji.r(14, 9), ji.r(7, 3), ji.r(2, 1)]

    for n in range(4, 12):
        right[n].volume = 0.67

    right[13].pitch = [ji.r(64, 63), ji.r(256, 189)]
    tw.prolong(14, F(1, 8), right)
    right[14].pitch = [ji.r(7, 3), ji.r(35, 16), ji.r(35, 12)]
    right[15].pitch = [ji.r(7, 4), ji.r(2, 1), ji.r(7, 3)]
    right[16].pitch = [ji.r(288, 245), ji.r(48, 49)]
    tw.eat(16, 17, right)
    right[17].pitch = [ji.r(192, 245), ji.r(256, 245)]
    tw.eat(17, 18, right)
    right[18].pitch = [ji.r(64, 63), ji.r(256, 189)]
    tw.eat(18, 19, right)
    right[19].pitch = [ji.r(36, 49)]
    right[20].pitch = [ji.r(256, 245)]


def _adapt_left_hand(left: lily.NOventLine, vm) -> None:
    tw.swap_duration(9, 10, F(1, 4), left)
    tw.swap_duration(20, 21, F(1, 4), left)
    tw.swap_duration(30, 31, F(1, 4), left)
    tw.swap_duration(40, 41, F(1, 4), left)
    for n in (6, 8, 10, 16, 18, 21, 27, 29, 31, 37, 39, 41):
        left[n].pitch = [left[n].pitch[0].register(keyboard.SYMBOLIC_GONG_OCTAVE)]
        left[n].pedal = attachments.Pedal(False)
        left[n].volume = 0.43
        left[n].ottava = attachments.Ottava(-1)

    tw.split(41, left, F(1, 4), F(1, 4))
    tw.split(31, left, F(1, 4), F(1, 4))
    tw.split(21, left, F(1, 4), F(1, 4))
    tw.split(10, left, F(1, 4), F(1, 4))

    tw.swap_duration(20, 19, F(1, 16), left)

    tw.crop(3, left, F(1, 16))
    left[3].pitch = [ji.r(7, 8)]

    left[10].pitch = [
        ji.r(35, 24).register(keyboard.SYMBOLIC_GONG_OCTAVE),
        ji.r(35, 128),
    ]
    left[10].ottava = attachments.Ottava(-1)
    left[10].arpeggio = None

    tw.add_kenong(12, left, ji.r(14, 9))

    left[13].pitch = [
        ji.r(64, 63).register(keyboard.SYMBOLIC_GONG_OCTAVE),
        ji.r(64, 63),
        ji.r(128, 189),
    ]
    tw.crop(15, left, F(1, 16))
    left[16].pitch = [ji.r(7, 8)]


def _adapt_violin2(violin: lily.NOventLine, vm) -> None:
    tw.crop(15, violin, F(1, 4), F(1, 8), F(1, 8))
    violin[15].pitch = [ji.r(3, 4)]
    tw.set_pizz(15, violin)

    violin[16].pitch = [ji.r(7, 9)]
    tw.set_arco(16, violin)
    violin[17].pitch = [ji.r(8, 9)]
    tw.set_arco(17, violin)

    tw.split_by_structure(23, 2, violin, vm, adapt_by_changed_structure=True)
    violin[24].acciaccatura = None
    violin[24].pitch = [ji.r(8, 9)]
    tw.set_pizz(24, violin)
    tw.crop(24, violin, F(1, 8))
    violin[25].pitch = [ji.r(7, 9)]
    tw.prolong(25, F(1, 16), violin)

    violin[26].pitch = [ji.r(288, 245)]
    tw.set_pizz(26, violin)
    violin[27].pitch = [ji.r(48, 35)]
    tw.set_pizz(27, violin)
    tw.crop(28, violin, F(1, 8), F(1, 8), F(2, 4))
    violin[28].pitch = [ji.r(288, 245)]
    tw.set_pizz(28, violin)
    violin[29].pitch = [ji.r(288, 245)]
    tw.set_arco(29, violin)
    tw.set_arco(30, violin)
    violin[30].pitch = [ji.r(48, 35)]
    tw.crop(30, violin, F(2, 8) + F(1, 16), F(1, 16), F(1, 8))
    violin[32].pitch = [ji.r(8, 9)]
    tw.set_pizz(32, violin)
    tw.rest(31, violin)

    """
    # tw.postpone(40, F(1, 4), violin)
    violin[38].ornamentation = None
    # tw.change_octave(38, 1, violin)
    tw.crop(38, violin, F(3, 8), F(1, 4))
    tw.rest(39, violin)
    tw.crop(39, violin, F(1, 4), F(1, 8), F(1, 8))
    violin[40].pitch = [ji.r(8, 9)]
    violin[41].pitch = [ji.r(7, 9)]
    tw.set_arco(40, violin)
    tw.set_arco(41, violin)

    tw.crop(42, violin, F(2, 8))
    violin[43].pitch = [ji.r(3, 4)]

    tw.crop(44, violin, F(1, 4))
    violin[44].pitch = [ji.r(64, 63)]
    tw.set_arco(44, violin)

    tw.crop(39, violin, F(1, 8))
    violin[40].pitch = [ji.r(64, 63)]
    tw.set_arco(40, violin)

    tw.crop(38, violin, F(1, 8), F(1, 8), F(1, 8))
    tw.rest(39, violin)

    tw.crop(37, violin, F(1, 4))
    violin[38].pitch = [ji.r(48, 35)]
    tw.set_arco(38, violin)
    violin[38].volume = 0.3

    tw.swap_duration(44, 43, F(1, 16), violin)
    tw.postpone(43, F(1, 16), violin)

    tw.crop(47, violin, F(1, 16))
    violin[48].pitch = [ji.r(8, 9)]
    """

    tw.shorten(38, F(3, 16), violin)
    violin[38].ornamentation = attachments.OrnamentationDown(2)

    # for n in range(41, 45):
    #     # tw.set_pizz(n, violin)
    #     tw.change_octave(n, 1, violin)

    tw.shorten(40, F(1, 16), violin)

    violin[42].acciaccatura = None
    tw.change_octave(42, -1, violin)
    tw.swap_duration(41, 42, F(1, 8), violin)
    tw.prolong(42, F(1, 4), violin)
    tw.crop(42, violin, F(3, 16), F(3, 16), F(1, 8))
    violin[43].pitch = [ji.r(7, 9)]
    violin[44].pitch = [ji.r(8, 9)]
    violin[46].pitch = [ji.r(7, 9)]
    tw.set_arco(46, violin)
    tw.prolong(46, F(1, 8), violin)
    violin[46].volume = 0.3
    tw.crop(46, violin, F(2, 16))
    violin[47].pitch = [ji.r(8, 9)]

    tw.set_pizz(47, violin)
    tw.set_pizz(46, violin)

    print("len(violin)", len(violin))

    tw.rest_many((52,), violin)
    tw.crop(51, violin, F(1, 8), F(3, 16), F(1, 16), F(3, 16), F(1, 16), F(3, 4))
    violin[51].pitch = [ji.r(7, 9)]
    violin[52].pitch = [ji.r(8, 9)]
    violin[53].pitch = [ji.r(7, 9)]
    violin[54].pitch = [ji.r(8, 9)]
    violin[55].pitch = [ji.r(35, 32)]
    violin[56].pitch = [ji.r(35, 32)]

    for n in range(51, 57):
        tw.set_pizz(n, violin)

    tw.shorten(50, F(1, 16), violin)
    tw.add_glissando(50, (1, 0, 0), violin, durations=[F(1, 8), F(1, 16)])

    tw.crop(39, violin, F(1, 16) + F(1, 4), F(1, 8))
    violin[40].pitch = [ji.r(48, 35)]
    tw.set_pizz(40, violin)


def _adapt_viola2(viola: lily.NOventLine, vm) -> None:
    tw.prolong(19, F(1, 32), viola)
    tw.crop(19, viola, F(1, 16), F(1, 16), F(1, 16), position=False)
    viola[21].pitch = [ji.r(8, 7)]
    viola[22].pitch = [ji.r(4, 3)]
    viola[23].pitch = [ji.r(8, 7)]

    for n in (20, 21, 22, 23):
        tw.set_pizz(n, viola)
        tw.change_octave(n, -1, viola)

    tw.rest_many((26, 27), viola)
    tw.prolong(24, F(1, 32), viola)
    tw.crop(25, viola, F(1, 8), F(2, 8) + F(1, 16), F(1, 16), F(1, 8))
    viola[26].pitch = [ji.r(4, 5)]
    tw.set_arco(26, viola)
    viola[28].pitch = [ji.r(2, 3)]
    tw.set_pizz(28, viola)
    tw.rest(27, viola)

    tw.set_pizz(33, viola)
    tw.change_octave(33, 1, viola)
    tw.prolong(33, F(5, 32), viola)
    tw.postpone(33, F(1, 8), viola)

    # print(viola[33:36])

    tw.crop(34, viola, F(1, 4) + F(1, 16), F(2, 16), F(1, 16))
    viola[35].pitch = [ji.r(48, 49)]
    viola[36].pitch = [ji.r(256, 245)]

    viola[37].pitch = [ji.r(48, 49)]
    viola[37].acciaccatura = None

    viola[38].pitch = [ji.r(256, 245)]
    tw.crop(38, viola, F(1, 16))
    viola[39].pitch = [ji.r(8, 7)]
    viola[40].acciaccatura = None
    tw.swap_duration(40, 39, F(1, 8), viola)

    tw.crop(41, viola, F(1, 8), F(1, 4))
    viola[41].pitch = [ji.r(7, 8)]
    viola[42].pitch = [ji.r(35, 48)]

    for n in (35, 36, 39, 41, 42):
        tw.set_arco(n, viola)

    viola[43].ornamentation = None
    tw.crop(43, viola, F(1, 8))
    viola[43].pitch = [ji.r(48, 49)]

    tw.shorten(42, F(1, 16), viola)
    viola[47].pitch = [ji.r(2, 3)]
    # tw.shorten(47, F(1, 32), viola)
    viola[48].pitch = [ji.r(35, 48)]
    tw.set_arco(46, viola)
    tw.set_arco(48, viola)
    tw.prolong(55, F(1, 32), viola)
    # tw.crop(55, viola, F(1, 16))
    viola[54].pitch = [ji.r(35, 48)]

    tw.split_by_structure(48, 2, viola, vm, adapt_by_changed_structure=True)
    viola[49].pitch = [ji.r(2, 3)]
    tw.set_pizz(49, viola)

    tw.rest_many((56, 55, 53, 52), viola)
    tw.crop(
        51,
        viola,
        F(1, 8),
        F(1, 4),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(3, 16),
        F(1, 16),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(1, 8),
        F(1, 8),
    )
    viola[52].pitch = [ji.r(35, 48)]
    viola[54].pitch = [ji.r(2, 3)]
    viola[56].pitch = [ji.r(2, 3)]
    viola[57].pitch = [ji.r(7, 8)]
    viola[58].pitch = [ji.r(35, 48)]

    for n in range(59, 64):
        viola[n].pitch = [ji.r(7, 8)]

    for n in (51, 53, 55, 56, 57, 58, 59, 60, 61, 62):
        if n == 51:
            tw.set_arco(n + 1, viola)
        else:
            tw.set_pizz(n + 1, viola)

    for idx, value in enumerate(np.linspace(1.1, 0.2, 5)):
        viola[59 + idx].volume = float(value)

    tw.shorten(52, F(1, 16), viola)
    tw.add_glissando(52, (1, 0, 0), viola, durations=[F(1, 8), F(1, 16)])


def _adapt_cello2(cello: lily.NOventLine, vm) -> None:
    tw.crop(12, cello, F(2, 8), F(1, 16), F(3, 16))
    cello[12].pitch = [ji.r(1, 2)]
    tw.set_pizz(12, cello)

    cello[14].pitch = [ji.r(7, 12)]
    tw.set_arco(14, cello)

    cello[21].glissando = None
    cello[21].pitch = [ji.r(256, 189).register(-1)]

    tw.swap_duration(20, 21, F(1, 16), cello)
    tw.set_arco(24, cello)
    tw.crop(24, cello, F(2, 8) + F(1, 16), F(1, 16), F(1, 8))
    tw.change_octave(24, -1, cello)
    cello[26].acciaccatura = None
    tw.set_pizz(26, cello)
    tw.rest(25, cello)

    tw.prolong(28, F(1, 32), cello)
    tw.crop(29, cello, F(3, 4), F(1, 8))
    cello[30].pitch = [ji.r(1, 1)]
    cello[30].natural_harmonic = attachments.NaturalHarmonic()
    tw.set_pizz(30, cello)

    tw.crop(31, cello, F(3, 8), F(1, 8) + F(3, 4))
    cello[32].pitch = [ji.r(72, 49)]
    tw.set_arco(32, cello)
    tw.add_artifical_harmonic(32, ji.r(72, 49).register(-2), cello)
    # cello[32].ornamentation = attachments.OrnamentationUp(2)

    # tw.postpone(33, F(1, 8), cello)
    # cello[34].glissando = None
    tw.rest(33, cello)
    tw.rest(34, cello)
    tw.crop(33, cello, F(1, 16), F(1, 16), F(1, 16), F(1, 16), F(1, 4))
    cello[34].pitch = [ji.r(1, 2)]
    cello[35].pitch = [ji.r(7, 12)]
    cello[36].pitch = [ji.r(7, 12)]
    cello[37].pitch = [ji.r(7, 24)]
    for n in range(34, 38):
        tw.set_pizz(n, cello)

    cello[38].pitch = [ji.r(72, 49).register(-2)]
    tw.set_arco(38, cello)

    for n in range(38, 40):
        tw.change_octave(n, 1, cello)

    tw.rest_many((41, 42, 44), cello)

    cello[46].pitch = [ji.r(7, 12)]
    tw.set_arco(46, cello)
    tw.swap_duration(45, 46, F(1, 8), cello)
    tw.shorten(46, F(2, 4) + F(1, 8), cello)

    tw.change_octave(42, 1, cello)
    tw.shorten(42, F(1, 4), cello)
    tw.set_arco(42, cello)

    print("len(cello)", len(cello))

    tw.rest_many((46, 45, 44), cello)
    tw.crop(
        43, cello, F(1, 8), F(3, 8), F(3, 16), F(1, 16), F(3, 16), F(1, 16), F(3, 8)
    )
    cello[44].pitch = [ji.r(7, 12)]
    cello[45].pitch = [ji.r(1, 2)]
    cello[46].pitch = [ji.r(7, 12)]
    cello[47].pitch = [ji.r(8, 15)]
    cello[49].pitch = [ji.r(7, 12)]

    tw.split(44, cello, F(1, 4), F(1, 8))

    for n in (44, 45, 46, 47, 48, 50):
        tw.set_pizz(n, cello)

    tw.set_arco(44, cello)
    tw.shorten(44, F(1, 16), cello)
    tw.add_glissando(44, (-1, 0, 0), cello, durations=[F(1, 8), F(1, 16)])


def _adapt_right2(right: lily.NOventLine, vm) -> None:
    tw.swap_duration(12, 13, F(1, 16), right)

    right[21].pitch = [ji.r(96, 35), ji.r(16, 5)]
    tw.eat(21, 22, right)
    tw.rest(22, right)
    tw.shorten(21, F(1, 32), right)

    tw.crop(20, right, F(1, 4), F(1, 16) + F(1, 4))
    right[20].pitch.append(ji.r(192, 245))

    right[24].pitch.append(ji.r(8, 5))
    tw.postpone(24, F(1, 8), right)

    tw.prolong(28, F(1, 4), right)
    tw.eat(28, 29, right)

    tw.rest_many((32, 33), right)

    right[30].pitch = [ji.r(48, 49), ji.r(288, 245)]

    tw.crop(31, right, F(1, 2))
    right[31].pitch = [ji.r(48, 49), ji.r(8, 7)]

    tw.eat(30, 29, right)

    tw.swap_duration(28, 29, F(1, 8), right)

    right[31].pitch = [ji.r(35, 16), ji.r(35, 12), ji.r(7, 3)]
    right[32].pitch = [ji.r(48, 49), ji.r(8, 7)]

    # tw.shorten(31, F(1, 16), right)
    tw.crop(32, right, F(1, 4))
    right[33].pitch = [ji.r(6, 7), ji.r(8, 7)]

    [tw.eat(35, 36, right) for _ in range(9)]
    right[35].pitch.extend([ji.r(7, 4), ji.r(35, 12)])

    print("right", len(right))

    tw.shorten(35, F(1, 1), right)
    tw.crop(36, right, F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 8), F(1, 4))
    right[36].pitch = [ji.r(7, 3), ji.r(35, 12)]
    right[37].pitch = [ji.r(14, 9), ji.r(2, 1)]
    right[38].pitch = [ji.r(2, 1)]
    right[39].pitch = [ji.r(14, 9), ji.r(2, 1)]
    right[40].pitch = [ji.r(16, 15)]
    right[41].pitch = [ji.r(7, 4), ji.r(14, 9)]
    right[42].pitch = [ji.r(7, 3), ji.r(35, 12)]

    tw.shorten(35, F(1, 4), right)


def _adapt_left2(left: lily.NOventLine, vm) -> None:
    tw.rest_many((25, 26), left)
    tw.add_gong(25, left, ji.r(16, 15))
    tw.rest(26, left)
    left[28].pitch.append(ji.r(1, 1))
    tw.prolong(28, F(2, 4), left)
    tw.postpone(27, F(1, 16), left)
    tw.shorten(25, F(1, 4), left)
    left[26].ottava = attachments.Ottava(0)
    left[26].pedal = attachments.Pedal(False)

    left[32].pitch = [ji.r(24, 49), ji.r(144, 245)]

    tw.add_kenong(34, left, ji.r(8, 7))
    tw.add_kenong(35, left, ji.r(1, 1))
    tw.add_kenong(36, left, ji.r(7, 6))

    left[34].arpeggio = None

    left[31].ottava = attachments.Ottava(0)
    left[31].pedal = attachments.Pedal(False)
    tw.crop(31, left, *([F(1, 16)] * 4))
    left[31].pitch = [ji.r(18, 49)]
    left[32].pitch = [ji.r(96, 245)]
    left[33].pitch = [ji.r(24, 49)]
    left[34].pitch = [ji.r(128, 245)]

    tw.eat(32, 31, left)

    left[40].pitch = [ji.r(3, 4), ji.r(4, 7)]
    tw.crop(41, left, F(1, 16))
    left[41].pitch = [ji.r(7, 9)]
    left[42].pitch = [ji.r(7, 8), ji.r(7, 6)]
    left[43].pitch = [ji.r(4, 3), ji.r(7, 9)]
    # left[43].arpeggio = None

    left[46].pitch = [ji.r(7, 18), ji.r(7, 24)]

    print("left", len(left))

    tw.eat(46, 47, left)
    tw.make_solo_gong(47, left)
    tw.add_kenong(48, left, ji.r(1, 1))
    tw.add_kenong(49, left, ji.r(16, 15))

    left[48].pitch = [ji.r(1, 4)]
    left[48].volume = 0.81
    left[49].pitch = [ji.r(4, 15)]
    left[49].volume = 0.83

    # tw.swap_duration(48, 47, F(1, 16), left)
    # tw.swap_duration(49, 48, F(1, 16), left)


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        1,
        tempo_factor=0.32,
        octave_of_first_pitch=-1,
        harmonic_tolerance=0.8,
        ro_temperature=0.712,
        ro_density=0.68,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.5, 0.05),
        area_density_reference_size=F(1, 2),
        area_min_split_size=F(3, 16),
    )

    vm.remove_area(0, 1)

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            tremolo_maker=infit.ActivityLevel(0),
            acciaccatura_maker=infit.ActivityLevel(6),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 0, 1)),
            harmonic_pitches_activity=0.6,
            harmonic_pitches_density=0.72,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 32),
            optional_pitches_avg_size=F(2, 16),
            optional_pitches_density=0.7,
            after_glissando_size=F(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(6, start_at=2),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2, 0, 1)),
            harmonic_pitches_activity=0.65,
            harmonic_pitches_density=0.72,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 32),
            optional_pitches_avg_size=F(1, 8),
            optional_pitches_density=0.7,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(8),
            acciaccatura_maker=infit.ActivityLevel(8),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 1)),
            shall_add_optional_pitches=True,
            harmonic_pitches_activity=0.69,
            harmonic_pitches_density=0.72,
            optional_pitches_min_size=F(1, 8),
            optional_pitches_avg_size=F(2, 16),
            optional_pitches_density=0.9,
        ),
        keyboard=keyboard.KeyboardMaker(
            lh_min_metricity_to_add_harmony=0.4,
            lh_min_metricity_to_add_accent=1.2,
            lh_max_metricity_for_arpeggio=0.35,
            lh_min_metricity_to_add_restricted_harmony=0,
            lh_prohibit_repetitions=False,
            lh_add_repetitions_avoiding_notes=False,
            rh_likelihood_making_harmony=1,
            harmonies_max_difference=1200,
            harmonies_min_difference=250,
            colotomic_structure=(0, 1, 1, 1),
        ),
    )

    _adapt_violin(vm.violin.musdat[1], vm)
    _adapt_viola(vm.viola.musdat[1], vm)
    _adapt_cello(vm.cello.musdat[1], vm)
    _adapt_keyboard(vm.keyboard.musdat[2], vm.keyboard.musdat[1], vm)

    vm.add_bar(5, abjad.TimeSignature((2, 4)))
    vm.add_bar(11, abjad.TimeSignature((2, 4)))
    vm.add_bar(13, abjad.TimeSignature((1, 4)))

    vm.force_remove_area(len(vm.violin.bars) - 1, len(vm.violin.bars))

    # second round of postprocessing
    _adapt_violin2(vm.violin.musdat[1], vm)
    _adapt_viola2(vm.viola.musdat[1], vm)
    _adapt_cello2(vm.cello.musdat[1], vm)
    _adapt_left2(vm.keyboard.musdat[2], vm)
    _adapt_right2(vm.keyboard.musdat[1], vm)

    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            nth_line = (2, 1)
        else:
            nth_line = (1,)

        novent_line = getattr(vm, instr).musdat[nth_line[0]]
        novent_line[0].dynamic = attachments.Dynamic("pp")

    for string in (vm.violin.musdat[1], vm.viola.musdat[1], vm.cello.musdat[1]):
        tw.detach_hauptstimme(string)

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

            # adapting accidental notation of keyboard
            if instr == "keyboard" and idx[1] == 0:
                abjad.Accidental.respell_with_sharps(staff[1])
                abjad.Accidental.respell_with_sharps(staff[2])
                abjad.Accidental.respell_with_sharps(staff[3])
                # abjad.Accidental.respell_with_sharps(staff[4])

                abjad.Accidental.respell_with_sharps(staff[7])
                abjad.Accidental.respell_with_flats(staff[8])

                abjad.Accidental.respell_with_sharps(staff[15][2:])

                abjad.attach(abjad.Tie(), staff[19][1])
                abjad.attach(abjad.Tie(), staff[19][2])

            elif instr == "keyboard" and idx[1] == 1:
                # abjad.Accidental.respell_with_sharps(staff[11])
                abjad.Accidental.respell_with_sharps(staff[1])
                abjad.Accidental.respell_with_sharps(staff[2])
                abjad.Accidental.respell_with_sharps(staff[3])
                # abjad.Accidental.respell_with_sharps(staff[4])

                # abjad.attach(abjad.Ottava(-1), staff[9][0])
                # tw.put_gong_to_separate_vox(9, 0, staff)

            elif instr == "violin":
                abjad.detach(abjad.Markup, staff[2][2])
                abjad.attach(
                    tw.scpm("arco sul tasto"), staff[2][2],
                )
                abjad.attach(
                    tw.scpm("molto sul tasto"), staff[3][2],
                )
                abjad.attach(abjad.StartHairpin(">"), staff[3][2])
                abjad.attach(abjad.Dynamic("ppp"), staff[4][0])
                abjad.attach(abjad.Dynamic("pp"), staff[4][1])
                abjad.detach(abjad.Markup, staff[5][1])
                abjad.attach(
                    tw.scpm("arco ordinario"), staff[5][1],
                )

            elif instr == "viola":
                abjad.attach(
                    abjad.StartTextSpan(left_text=abjad.Markup("rit.")), staff[-1][0]
                )
                abjad.attach(abjad.StopTextSpan(), staff[-1][-1])
                abjad.attach(abjad.StartHairpin(">"), staff[-1][0])
                abjad.attach(abjad.Dynamic("ppp"), staff[-1][-1])

    return verse
