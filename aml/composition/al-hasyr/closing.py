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

ARCO = attachments.StringContactPoint("arco")
PIZZ = attachments.StringContactPoint("pizzicato")
FLAUTANDO = abjad.Markup(
    abjad.MarkupCommand("italic", ["flautando"]), direction=abjad.enums.Up
)

#####################################################
#            post processing functions              #
#####################################################


def _adapt_violin(violin: lily.NOventLine, vm) -> None:
    tw.change_octave(4, 1, violin)
    tw.change_octave(5, 1, violin)
    tw.change_octave(6, -1, violin)
    tw.change_octave(7, -1, violin)
    violin[7].optional = None
    violin[7].volume = 1.2
    tw.split_by_structure(5, 3, violin, vm, adapt_by_changed_structure=True)
    violin[6].pitch = [ji.r(16, 9).register(0)]
    tw.split_by_structure(3, 2, violin, vm, adapt_by_changed_structure=True)
    tw.split_by_structure(1, 2, violin, vm, adapt_by_changed_structure=True)
    violin[2].acciaccatura = None
    violin[5].acciaccatura = None

    tw.swap_duration(7, 8, F(1, 32), violin)
    tw.swap_duration(8, 9, F(3, 16), violin)
    tw.crop(10, violin, F(1, 4))
    violin[11].acciaccatura = None
    violin[11].pitch = [ji.r(48, 35)]

    tw.crop(9, violin, F(1, 16), F(1, 16))
    violin[9].pitch = [ji.r(64, 63).register(1)]
    violin[10].pitch = [ji.r(16, 9).register(0)]
    tw.add_glissando(8, (0, 1), violin)
    tw.add_glissando(9, (0, -1), violin)

    tw.crop(17, violin, F(4, 4), F(3, 4), F(2, 4))

    violin[17].pitch = [ji.r(35, 32).register(0)]
    violin[18].pitch = [ji.r(3, 2).register(-1)]
    violin[19].pitch = [ji.r(288, 245).register(0)]

    tw.crop(20, violin, F(7, 4) + F(1, 8), F(1, 4), F(1, 8))

    for n in (17, 18, 19, 21, 22):
        violin[n].string_contact_point = ARCO
        violin[n].volume = 0.5

    for n in (21, 22, 26):
        violin[n].string_contact_point = PIZZ
        violin[n].volume = 1.2

    violin[21].pitch = [ji.r(3, 2).register(0)]
    violin[22].pitch = [ji.r(35, 32).register(0)]

    for n in (24, 25, 26):
        tw.change_octave(n, 1, violin)

    tw.swap_duration(23, 24, F(1, 16), violin)
    violin[25].acciaccatura = None
    violin[26].acciaccatura = None
    tw.swap_duration(23, 24, F(1, 8), violin)
    tw.add_glissando(24, (2, 0, 0), violin, durations=[F(1, 8), F(1, 4)])
    violin[25].pitch = [ji.r(48, 35)]

    tw.prolong(26, F(1, 32), violin)
    tw.crop(27, violin, F(2, 4), F(1, 4))

    violin[28].pitch = [ji.r(35, 32)]
    violin[28].volume = 0.5
    violin[28].string_contact_point = ARCO

    tw.crop(29, violin, F(1, 4))

    violin[29].pitch = [ji.r(48, 35)]
    violin[29].volume = 1.2
    violin[29].string_contact_point = PIZZ

    tw.crop(27, violin, F(1, 8), position=False)
    violin[28].pitch = [ji.r(14, 9)]
    violin[28].volume = 0.5
    violin[28].string_contact_point = ARCO

    tw.crop(25, violin, F(1, 8), position=False)
    violin[26].pitch = [ji.r(3, 2)]
    violin[26].string_contact_point = PIZZ
    violin[26].volume = 1.2

    tw.crop(31, violin, F(1, 8))
    violin[31].pitch = [ji.r(3, 2)]

    tw.crop(31, violin, F(1, 8))

    # tw.eat(33, 34, violin)
    tw.eat(34, 35, violin)

    violin[35].optional = None

    tw.crop(35, violin, F(1, 8))

    violin[36].pitch = [ji.r(48, 35)]
    violin[36].volume = 0.4
    # violin[36].string_contact_point = ARCO
    violin[36].acciaccatura = None

    violin[39].pitch = [ji.r(3, 4)]
    violin[39].volume = 0.6
    violin[39].string_contact_point = ARCO

    tw.swap_duration(38, 39, F(3, 32), violin)
    tw.crop(39, violin, F(1, 8))
    tw.rest(40, violin)
    tw.eat(39, 38, violin)
    # tw.swap_duration(39, 40, F(1, 4), violin)

    violin[39].pitch = [ji.r(288, 245)]
    violin[39].volume = 0.6
    violin[39].string_contact_point = ARCO

    tw.swap_duration(42, 41, F(1, 16), violin)

    tw.eat(39, 40, violin)
    tw.crop(40, violin, F(1, 8))

    for n in (41, 43):
        violin[n].string_contact_point = PIZZ
        violin[n].volume = 2

    violin[41].hauptstimme = attachments.Hauptstimme(True, False)
    violin[42].hauptstimme = attachments.Hauptstimme(True, False)
    violin[43].hauptstimme = attachments.Hauptstimme(False, False)
    violin[44].hauptstimme = attachments.Hauptstimme(False, False)
    violin[45].hauptstimme = attachments.Hauptstimme(False, True)
    violin[46].hauptstimme = None

    tw.eat(39, 40, violin)
    tw.add_glissando(39, (0, 0, -2, -2), violin, durations=[F(1, 4), F(1, 8), F(1, 8)])

    tw.crop(47, violin, F(1, 8), F(2, 4) + F(4, 4), F(1, 4) + F(0, 8), F(3, 8))

    for n in (48, 50):
        violin[n].pitch = [ji.r(288, 245)]
        if n == 50:
            violin[n].string_contact_point = PIZZ
            violin[n].volume = 1.8
        else:
            violin[n].string_contact_point = ARCO
            violin[n].volume = 0.55

    tw.split_by_structure(
        48, 5, violin, vm, adapt_by_changed_structure=True, set_n_novents2rest=2
    )

    tw.crop(45, violin, F(1, 8))
    tw.crop(46, violin, F(2, 4), F(1, 8), F(1, 8))

    violin[45].pitch = [ji.r(7, 9)]

    violin[47].pitch = [ji.r(288, 245)]
    violin[48].pitch = [ji.r(48, 35)]
    violin[49].pitch = [ji.r(14, 9)]

    for n in (44, 45, 47, 48, 49):
        violin[n].volume = 1.5
        violin[n].string_contact_point = PIZZ

    # tw.swap_duration(51, 52, F(1, 8), violin)
    tw.shorten(52, F(1, 8), violin)
    tw.rest(55, violin)

    tw.rest(60, violin)
    tw.crop(59, violin, F(5, 8), F(1, 8))

    violin[60].pitch = [ji.r(48, 35)]
    violin[61].pitch = [ji.r(288, 245)]
    violin[62].pitch = [ji.r(8, 9)]

    for n in (60, 61):
        violin[60].volume = 0.4
        violin[60].string_contact_point = ARCO

    for n in (66, 67):
        violin[n].glissando = None
        violin[n].acciaccatura = None
        violin[n].string_contact_point = PIZZ
        violin[n].volume = 1.5

    tw.swap_duration(55, 56, F(1, 16), violin)
    tw.crop(56, violin, F(1, 16), F(1, 8))
    violin[56].pitch = [ji.r(3, 2)]
    violin[57].pitch = [ji.r(48, 35)]

    tw.crop(59, violin, F(1, 8), F(1, 8), position=False)

    violin[60].pitch = [ji.r(3, 4)]
    violin[61].pitch = [ji.r(8, 9)]
    violin[62].pitch = [ji.r(3, 2)]
    for n in (60, 61, 62):
        violin[n].volume = 1.5
        violin[n].string_contact_point = PIZZ

    tw.rest_many((70, 71, 72, 74), violin)

    tw.crop(
        69,
        violin,
        F(1, 32) + F(3, 4),
        F(5, 4),
        F(2, 4),
        F(1, 4),
        F(3, 4),
        F(1, 4),
        F(2, 4),
    )

    tw.swap_duration(68, 69, F(1, 32), violin)

    violin[69].pitch = [ji.r(288, 245).register(1)]
    violin[70].pitch = [ji.r(48, 35).register(0)]
    violin[71].pitch = [ji.r(288, 245).register(0)]
    violin[73].pitch = [ji.r(3, 2).register(0)]
    violin[74].pitch = [ji.r(8, 9).register(-1)]
    violin[76].pitch = [ji.r(7, 9).register(-1)]

    for n in (69, 70, 71, 73, 74, 76):
        violin[n].string_contact_point = attachments.StringContactPoint(
            "molto sul tasto"
        )
        violin[n].volume = 0.3

    violin[69].string_contact_point = attachments.StringContactPoint("sul tasto")

    # for n in (70, 71):
    #     tw.change_octave(n, 1, violin)

    violin[76].volume = 0.4

    tw.change_octave(66, 1, violin)
    tw.change_octave(68, 1, violin)
    violin[68].acciaccatura = None
    # tw.crop(68, violin, F(1, 8), position=False)
    # violin[69].pitch = [ji.r(48, 35).register(1)]

    # tw.crop(65, violin, F(1, 32), position=False)
    # violin[66].pitch = [ji.r(3, 2)]
    violin[66].pitch = [ji.r(14, 9)]
    violin[67].pitch = [ji.r(16, 9)]
    tw.set_arco(66, violin)
    tw.set_arco(67, violin)
    """
    tw.postpone(69, F(1, 16), violin)
    """

    print("violin", len(violin))
    violin[-1].fermata = attachments.Fermata("longfermata")

    tw.crop(0, violin, F(1, 8), F(1, 8))
    violin[1].pitch = [ji.r(3, 4)]
    violin[2].pitch = [ji.r(7, 9)]
    tw.set_pizz(1, violin)
    tw.set_pizz(2, violin)

    tw.swap_duration(2, 3, F(1, 32), violin)

    # tw.rest(1, violin)
    tw.eat(1, 0, violin)
    # tw.crop(4, violin, F(1, 8), F(1, 4))
    # violin[5].pitch = [ji.r(48, 35)]
    # tw.set_pizz(5, violin)

    for n in range(17, 21):
        violin[n].string_contact_point = attachments.StringContactPoint(
            "arco sul tasto"
        )

    for n in range(25, 27):
        violin[n].string_contact_point = attachments.StringContactPoint(
            "arco ordinario"
        )

    for n in range(30, 32):
        violin[n].dynamic = attachments.Dynamic('ppp')
        violin[n].string_contact_point = attachments.StringContactPoint(
            "arco sul tasto"
        )

    violin[32].dynamic = attachments.Dynamic('pp')

    for n in range(36, 38):
        violin[n].string_contact_point = attachments.StringContactPoint(
            "arco sul ponticello"
        )

    for n in range(39, 41):
        violin[n].string_contact_point = attachments.StringContactPoint("ordinario")


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    viola[1].pitch = viola[1].pitch[:1]
    viola[1].choose = False
    viola[1].optional = False
    viola[1].volume = 0.65
    tw.prolong(1, F(1, 4), viola)
    tw.crop(1, viola, F(1, 4))
    viola[1].pitch = [ji.r(35, 48)]
    viola[2].string_contact_point = PIZZ
    viola[2].volume = 2
    tw.crop(3, viola, F(1, 4))
    viola[4].pitch = [ji.r(48, 49).register(-2)]
    viola[6].pitch = [ji.r(4, 7)]
    viola[8].pitch = [ji.r(35, 48)]

    tw.prolong(9, F(1, 4), viola)
    tw.crop(9, viola, F(1, 8), F(1, 8), F(3, 16), F(1, 16))
    viola[9].pitch = [ji.r(48, 49)]
    viola[11].pitch = [ji.r(35, 48)]
    viola[12].pitch = [ji.r(4, 7)]

    for n in (4, 5, 6, 7, 8, 9, 10, 11, 12):
        if n < 9:
            tw.change_octave(n, 1, viola)
        viola[n].string_contact_point = ARCO
        viola[n].volume = 0.75
        viola[n].optional = None
        viola[n].acciaccatura = None

    # tw.add_glissando(9, (0, -1), viola)

    tw.change_octave(13, -1, viola)
    viola[13].optional = None
    viola[13].volume = 0.65

    tw.crop(14, viola, F(1, 4))
    viola[14].pitch = [ji.r(48, 49)]
    viola[14].volume = 2
    viola[14].string_contact_point = PIZZ

    viola[16].acciaccatura = None
    tw.rest_many((18, 20), viola)

    tw.prolong(16, F(1, 4), viola)

    tw.crop(17, viola, F(3, 4), F(2, 4))
    viola[17].pitch = [ji.r(4, 7)]
    viola[18].pitch = [ji.r(48, 49)]

    for n in (17, 18):
        viola[n].string_contact_point = ARCO
        viola[n].volume = 0.5

    viola[22].acciaccatura = None
    viola[24].acciaccatura = None

    tw.shorten(24, F(3, 16), viola)

    for n in (22, 23, 24):
        tw.change_octave(n, 1, viola)
        viola[n].glissando = None
        viola[n].string_contact_point = PIZZ
        viola[n].volume = 1

    tw.swap_duration(23, 21, F(1, 8), viola)

    tw.crop(25, viola, F(1, 4), F(1, 2), F(1, 4))

    viola[26].pitch = [ji.r(4, 5)]
    viola[26].string_contact_point = ARCO
    viola[26].volume = 0.6

    viola[27].pitch = [ji.r(7, 8)]
    viola[27].string_contact_point = PIZZ
    viola[27].volume = 1

    tw.rest(20, viola)
    tw.crop(26, viola, F(1, 8), position=False)
    viola[27].pitch = [ji.r(7, 8)]
    viola[27].volume = 0.7
    viola[27].string_contact_point = ARCO

    viola[28].acciaccatura = None

    viola[29].string_contact_point = PIZZ
    viola[29].volume = 1.9

    tw.crop(24, viola, F(1, 8), position=False)

    viola[25].string_contact_point = PIZZ
    viola[25].volume = 1.9
    viola[25].pitch = [ji.r(8, 7)]

    tw.prolong(30, F(3, 4), viola)

    viola[31].string_contact_point = PIZZ
    viola[31].volume = 2
    viola[31].pitch = [ji.r(7, 8)]

    tw.crop(30, viola, F(1, 8))
    tw.crop(32, viola, F(1, 8), position=False)
    viola[33].pitch = [ji.r(7, 4).register(-1)]
    viola[33].string_contact_point = ARCO
    viola[33].volume = 0.7

    viola[36].pitch = [ji.r(8, 5).register(-1)]
    viola[36].string_contact_point = ARCO
    viola[36].volume = 0.7
    tw.eat(36, 37, viola)

    viola[34].glissando = None
    tw.add_glissando(34, (0, 0, 2), viola, durations=[F(1, 4), F(1, 8)])
    # tw.change_octave(35, -1, viola)
    tw.split_by_structure(36, 3, viola, vm, adapt_by_changed_structure=True)

    viola[37].pitch = [ji.r(256, 245).register(-1)]
    viola[38].pitch = [ji.r(8, 5).register(-1)]
    # viola[40].pitch = [ji.r(8, 7).register(-1)]

    for n in (
        37,
        38,
    ):
        viola[n].volume = 0.55
        viola[n].string_contact_point = ARCO

    tw.change_octave(42, -1, viola)

    viola[44].acciaccatura = None

    tw.crop(35, viola, F(1, 8))

    for n in (36, 37, 38):
        viola[n].string_contact_point = PIZZ
        viola[n].volume = 1.4

    tw.eat(34, 35, viola)
    tw.add_glissando(34, (0, 0, 2, 2), viola, durations=[F(1, 4), F(1, 8), F(1, 8)])

    tw.crop(52, viola, F(2, 4) + F(1, 8), F(2, 8))

    viola[53].pitch = [ji.r(48, 49)]
    # viola[53].ornamentation = attachments.OrnamentationUp(1)

    for n in (46, 47, 49, 53):
        if n == 53:
            viola[n].string_contact_point = PIZZ
            viola[n].volume = 1.5
        else:
            viola[n].string_contact_point = ARCO
            viola[n].volume = 0.66
        viola[n].optional = None

    viola[51].optional = None
    viola[51].choose = None
    viola[51].volume = 0.66
    viola[51].pitch = [ji.r(256, 245)]

    tw.swap_duration(41, 42, F(1, 16), viola)
    viola[41].pitch = [ji.r(4, 7)]
    tw.swap_duration(40, 41, F(1, 8), viola)

    for n in (40, 41):
        viola[n].string_contact_point = PIZZ
        viola[n].volume = 1.4

    tw.add_glissando(38, (0, 0, -2), viola, durations=[F(1, 8), F(1, 8)])

    tw.split(43, viola, F(1, 4), F(1, 8), F(1, 8))

    for n in (44, 45, 46):
        viola[n].volume = 1.5
        viola[n].string_contact_point = PIZZ

    viola[45].pitch = [ji.r(8, 7)]
    viola[46].pitch = [ji.r(4, 3)]

    tw.change_octave(59, 1, viola)

    tw.crop(59, viola, F(1, 8))
    viola[60].pitch = [ji.r(4, 3)]
    viola[60].string_contact_point = PIZZ
    viola[60].volume = 1.25

    viola[62].string_contact_point = ARCO
    viola[62].volume = 0.5
    viola[62].optional = None
    tw.prolong(62, F(1, 8), viola)
    tw.crop(62, viola, F(1, 8), F(1, 8))
    viola[63].pitch = [ji.r(35, 48)]
    viola[64].pitch = [ji.r(7, 8)]

    viola[65].string_contact_point = ARCO
    viola[65].volume = 0.5
    viola[65].pitch = [ji.r(48, 49)]

    viola[66].acciaccatura = None
    tw.change_octave(66, 1, viola)

    tw.split_by_structure(69, 2, viola, vm, adapt_by_changed_structure=True)
    viola[69].pitch = [ji.r(4, 3)]
    viola[70].pitch = [ji.r(48, 49)]

    viola[71].pitch = [ji.r(256, 245).register(-1)]
    viola[71].string_contact_point = ARCO
    viola[71].volume = 0.5

    tw.rest(72, viola)
    tw.rest(73, viola)

    tw.crop(72, viola, F(1, 4) + F(3, 16), F(1, 16))
    viola[73].pitch = [ji.r(35, 24).register(-1)]
    viola[73].string_contact_point = PIZZ
    viola[73].volume = 1.4

    tw.rest(52, viola)

    tw.crop(51, viola, F(1, 16), position=False)
    viola[52].pitch = [ji.r(256, 245)]
    viola[52].string_contact_point = PIZZ
    viola[52].volume = 1.5

    viola[60].pitch = [ji.r(7, 8)]
    viola[60].string_contact_point = PIZZ
    viola[60].volume = 1.5

    tw.rest_many((72, 74, 76, 78), viola)

    tw.crop(
        71,
        viola,
        F(1, 4) + F(3, 4),
        F(2, 4),
        F(2, 4),
        F(4, 4),
        F(4, 4),
        F(2, 4),
        F(2, 4),
    )
    viola[71].pitch = [ji.r(48, 49).register(0)]
    viola[72].pitch = [ji.r(8, 5).register(0)]
    viola[73].pitch = [ji.r(256, 245).register(0)]
    viola[74].pitch = [ji.r(48, 49).register(-1)]
    viola[75].pitch = [ji.r(7, 4).register(-1)]
    viola[76].pitch = [ji.r(8, 5).register(-1)]
    viola[77].pitch = [ji.r(4, 3).register(-1)]

    for n in range(71, 78):
        viola[n].string_contact_point = attachments.StringContactPoint(
            "molto sul tasto"
        )
        viola[n].volume = 0.3

    viola[71].string_contact_point = attachments.StringContactPoint("sul tasto")

    tw.change_octave(69, 1, viola)
    tw.change_octave(70, 2, viola)

    viola[67].pitch = [ji.r(8, 7)]
    tw.set_arco(67, viola)

    tw.eat(68, 67, viola)
    # tw.crop(67, viola, F(1, 8), position=False)
    # viola[68].pitch = [ji.r(8, 5)]

    """
    tw.postpone(71, F(1, 4), viola)
    """

    print("viola", len(viola))
    viola[-1].fermata = attachments.Fermata("longfermata")

    tw.crop(2, viola, F(1, 4))
    viola[3].pitch = [ji.r(48, 49)]
    tw.set_pizz(3, viola)

    for n in range(16, 19):
        viola[n].string_contact_point = attachments.StringContactPoint("arco sul tasto")

    viola[24].string_contact_point = attachments.StringContactPoint("arco ordinario")

    for n in range(28, 30):
        viola[n].string_contact_point = attachments.StringContactPoint("arco sul tasto")
        viola[n].dynamic = attachments.Dynamic('ppp')

    viola[30].dynamic = attachments.Dynamic('pp')

    for n in range(33, 35):
        viola[n].string_contact_point = attachments.StringContactPoint("arco ordinario")


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    tw.change_octave(1, 1, cello)
    cello[1].optional = False
    cello[1].volume = 0.6
    tw.prolong(1, F(2, 8), cello)
    tw.crop(1, cello, F(1, 8), position=False)
    cello[2].acciaccatura = None
    cello[2].string_contact_point = PIZZ
    cello[2].pitch = [ji.r(1, 2)]
    cello[2].volume = 1.2
    # tw.change_octave(4, 1, cello)
    cello[4].volume = 0.6
    cello[5].pitch = [ji.r(7, 12)]
    # cello[5].string_contact_point = PIZZ
    # cello[5].volume = 1.9
    cello[5].string_contact_point = ARCO
    cello[5].volume = 0.5
    cello[6].volume = 0.56
    cello[6].natural_harmonic = attachments.NaturalHarmonic()
    tw.change_octave(6, 2, cello)
    cello[9].acciaccatura = None
    tw.shorten(9, F(3, 32), cello)

    tw.crop(7, cello, F(1, 16))
    tw.swap_duration(9, 8, F(1, 16), cello)
    cello[8].pitch = [ji.r(72, 49).register(-1)]
    cello[8].string_contact_point = ARCO
    cello[8].volume = 0.5
    cello[9].glissando = None

    cello[12].acciaccatura = None
    tw.copy_pitch(10, 12, cello)

    tw.crop(11, cello, F(1, 16), position=False)
    cello[12].string_contact_point = ARCO
    cello[12].volume = 0.5
    cello[12].pitch = [ji.r(72, 49).register(-1)]
    tw.crop(13, cello, F(1, 8), position=False)
    tw.prolong(14, F(1, 8), cello)
    cello[14].pitch = [ji.r(7, 6).register(-1)]

    tw.rest_many((15, 17, 18, 20, 21, 23), cello)
    tw.crop(15, cello, F(3, 4), F(3, 4), F(2, 4))

    cello[16].pitch = [ji.r(12, 7).register(-2)]
    cello[17].pitch = [ji.r(72, 49).register(-1)]

    for n in (16, 17):
        cello[n].string_contact_point = ARCO
        cello[n].volume = 0.5

    tw.prolong(14, F(3, 4), cello)
    tw.rest_many((18, 19, 21, 23), cello)

    tw.crop(
        17,
        cello,
        F(7, 4) + F(1, 8),
        F(1, 4),
        F(1, 8),
        F(1, 4),
        F(1, 4),
        F(1, 2),
        F(1, 4),
    )

    cello[18].pitch = [ji.r(12, 7).register(-1)]
    cello[19].pitch = [ji.r(7, 6).register(-1)]
    cello[20].pitch = [ji.r(16, 15).register(-1)]
    cello[22].pitch = [ji.r(1, 1).register(-1)]
    cello[23].pitch = [ji.r(7, 6).register(-2)]

    for n in (18, 19, 20, 23):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.2

    for n in (22,):
        cello[n].string_contact_point = ARCO
        cello[n].volume = 0.4

    tw.swap_duration(25, 24, F(1, 4), cello)
    tw.prolong(25, F(1, 16), cello)

    tw.crop(26, cello, F(1, 8))
    tw.change_octave(27, -1, cello)
    cello[27].string_contact_point = PIZZ
    cello[27].volume = 1.2

    tw.rest_many((29, 31), cello)

    tw.crop(22, cello, F(1, 8), position=False)
    cello[23].string_contact_point = PIZZ
    cello[23].volume = 2
    cello[23].pitch = [ji.r(1, 4)]

    tw.prolong(28, F(1, 8) + F(3, 4), cello)

    cello[29].pitch = [ji.r(1, 4)]
    cello[29].volume = 2
    cello[29].string_contact_point = PIZZ
    [tw.eat(29, 30, cello) for _ in range(2)]

    tw.crop(28, cello, F(1, 8))
    cello[29].pitch = [ji.r(16, 15).register(-2)]

    tw.swap_duration(32, 33, F(1, 8), cello)

    cello[33].pitch = [ji.r(256, 189).register(-1)]
    cello[33].volume = 0.3
    cello[33].string_contact_point = ARCO
    # tw.add_artifical_harmonic(33, ji.r(256, 189).register(-2), cello)

    tw.swap_duration(34, 33, F(1, 16), cello)

    tw.crop(33, cello, F(1, 8))
    tw.rest(33, cello)

    cello[36].pitch = [ji.r(384, 245).register(-1)]
    cello[36].volume = 0.4
    cello[36].string_contact_point = ARCO

    cello[31].ornamentation = attachments.OrnamentationUp(3)

    for n in (34, 35, 36):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.5

    for n in (40, 41, 43):
        cello[n].acciaccatura = None
        tw.change_octave(n, -1, cello)
        cello[n].artifical_harmonic = None

    tw.crop(52, cello, F(1, 8), F(2, 16), F(2, 16), F(3, 8))
    cello[55].pitch = [ji.r(72, 49).register(-1)]
    cello[55].volume = 0.6
    cello[55].string_contact_point = ARCO

    tw.prolong(43, F(1, 32), cello)

    tw.prolong(38, F(1, 8), cello)

    tw.crop(43, cello, F(1, 8))

    cello[43].pitch = [ji.r(384, 245).register(-1)]
    cello[44].pitch = [ji.r(6, 7)]
    for n in (38, 39, 43, 44, 45):
        cello[n].string_contact_point = PIZZ
        cello[n].volume = 1.4

    for n in (48, 52, 53, 54):
        if n == 53:
            cello[n].pitch = [ji.r(384, 245).register(-1)]
        else:
            cello[n].pitch = [ji.r(6, 7)]
        cello[n].volume = 0.4
        cello[n].string_contact_point = ARCO

    # tw.eat(53, 54, cello)

    # tw.add_glissando(51, (0, 0, 2), cello, durations=[F(3, 16), F(1, 8)])
    # tw.add_glissando(52, (0, -2), cello)
    cello[51].acciaccatura = None

    tw.shorten(51, F(1, 8), cello)

    [tw.rest(58, cello) for _ in range(3)]

    tw.crop(
        57,
        cello,
        F(1, 4),
        F(1, 8),
        F(1, 8),
        F(1, 16),
        F(3, 16),
        F(1, 8),
        F(1, 8),
        position=False,
    )

    for n, pitch in (
        (58, ji.r(7, 6)),
        (59, ji.r(1, 1)),
        (60, ji.r(16, 15)),
        (61, ji.r(1, 1)),
        (62, ji.r(1, 4)),
    ):
        if n != 62:
            tw.add_artifical_harmonic(n, pitch + ji.r(1, 2), cello)
        cello[n].pitch = [pitch + ji.r(2, 1)]
        if n == 62:
            cello[n].string_contact_point = PIZZ
            cello[n].volume = 1.6
        else:
            cello[n].string_contact_point = ARCO
            cello[n].volume = 0.4

    cello[63].pitch = [ji.r(8, 15)]
    cello[63].string_contact_point = PIZZ
    cello[63].volume = 1.25

    for n in (64, 67):
        cello[n].string_contact_point = ARCO
        cello[n].volume = 0.45

    tw.split(64, cello, F(3, 16), F(1, 16))
    cello[64].pitch = [ji.r(7, 12)]
    cello[65].pitch = [ji.r(1, 2)]

    cello[67].pitch = [ji.r(384, 245).register(-1)]
    cello[68].pitch = [ji.r(72, 49).register(-1)]

    cello[70].acciaccatura = None
    tw.change_octave(70, 1, cello)

    cello[71].pitch = [ji.r(72, 49).register(-1)]
    cello[71].string_contact_point = ARCO
    cello[71].volume = 0.45

    [tw.eat(71, 72, cello) for _ in range(2)]

    tw.crop(71, cello, F(1, 8))
    cello[72].pitch = [ji.r(384, 245).register(-1)]

    tw.shorten(73, F(3, 16), cello)

    cello[75].optional = None
    cello[75].acciaccatura = None
    cello[75].string_contact_point = PIZZ
    cello[75].volume = 1.5
    tw.swap_duration(74, 75, F(1, 16), cello)

    cello[56].string_contact_point = PIZZ
    cello[56].volume = 1.5
    tw.crop(56, cello, F(1, 8))
    cello[56].pitch = [ji.r(384, 245).register(-1)]
    cello[55].pitch = [ji.r(72, 49).register(-1)]

    tw.rest(51, cello)

    cello[63].string_contact_point = PIZZ
    cello[63].volume = 1.4

    tw.rest_many((74, 76, 78, 80), cello)

    print("cello", len(cello))

    tw.prolong(72, F(1, 16) + F(1, 4), cello)
    tw.crop(
        73,
        cello,
        F(2, 4),
        F(1, 4),
        F(1, 4),
        F(2, 4),
        F(1, 4),
        F(1, 4),
        F(1, 4),
        F(2, 4),
        F(7, 4),
    )

    tw.swap_duration(72, 71, F(1, 16), cello)

    cello[72].pitch = [ji.r(72, 49).register(1)]
    cello[73].pitch = [ji.r(384, 245).register(0)]
    cello[75].pitch = [ji.r(16, 15).register(0)]
    cello[76].pitch = [ji.r(384, 245).register(0)]
    cello[78].pitch = [ji.r(12, 7).register(0)]
    cello[79].pitch = [ji.r(72, 49).register(0)]
    cello[80].pitch = [ji.r(7, 6).register(0)]
    cello[81].pitch = [ji.r(1, 1).register(0)]

    for n in (72, 73, 75, 76, 78, 79, 80, 81):
        cello[n].string_contact_point = attachments.StringContactPoint(
            "molto sul tasto"
        )
        cello[n].volume = 0.3

    cello[72].string_contact_point = attachments.StringContactPoint("sul tasto")
    cello[69].pitch = [ji.r(7, 6).register(0)]

    tw.change_octave(75, 1, cello)

    for n in (72, 73, 75, 76, 78, 79):
        tw.add_artifical_harmonic(n, cello[n].pitch[0] - ji.r(4, 1), cello)

    cello[81].natural_harmonic = attachments.NaturalHarmonic()

    """
    tw.postpone(72, F(1, 8), cello)
    """

    tw.crop(0, cello, F(1, 8), F(1, 8))
    cello[1].pitch = [ji.r(1, 2)]
    cello[2].pitch = [ji.r(7, 12)]
    tw.set_pizz(1, cello)
    tw.set_pizz(2, cello)

    tw.swap_duration(2, 3, F(1, 32), cello)

    tw.crop(5, cello, F(1, 4))
    cello[5].pitch = [ji.r(3, 7)]
    tw.set_pizz(5, cello)

    for n in range(15, 20):
        cello[n].string_contact_point = attachments.StringContactPoint("sul tasto")

    cello[25].string_contact_point = attachments.StringContactPoint("arco ordinario")

    for n in range(29, 31):
        cello[n].string_contact_point = attachments.StringContactPoint("arco sul tasto")
        cello[n].dynamic = attachments.Dynamic('ppp')

    cello[31].dynamic = attachments.Dynamic('pp')

    for n in range(34, 36):
        cello[n].string_contact_point = attachments.StringContactPoint("arco ordinario")


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine, vm) -> None:
    tw.swap_duration(0, 1, F(7, 32), right)
    tw.prolong(1, F(2, 8), right)
    # right[2].pitch = [ji.r(256, 245)]
    tw.swap_duration(7, 8, F(1, 16), right)
    tw.prolong(8, F(1, 8), right)
    tw.rest_many((14, 15, 17), right)
    tw.prolong(12, F(3, 4), right)
    tw.crop(13, right, F(3, 4), F(2, 4))
    # tw.change_octave(12, -1, right)
    right[13].pitch = [ji.r(3, 4)]
    right[14].pitch = [ji.r(72, 49).register(-1)]

    tw.swap_duration(17, 18, F(2, 4), right)
    tw.swap_duration(20, 21, F(1, 16), right)
    tw.rest(28, right)

    right[26].optional_some_pitches = None
    tw.prolong(26, F(2, 4) + F(1, 16), right)

    tw.rest(28, right)

    tw.swap_duration(32, 31, F(1, 16), right)

    tw.rest(32, right)
    tw.swap_duration(31, 32, F(1, 8), right)

    tw.prolong(28, F(1, 32), right)
    right[28].optional_some_pitches = None

    for n in (38, 39, 40, 42):
        right[n].optional_some_pitches = None

    tw.swap_duration(45, 44, F(1, 32), right)

    for n in (46,):
        right[n].optional_some_pitches = None

    # tw.swap_duration(48, 49, F(1, 4), right)
    tw.rest(49, right)
    right[49].pitch = [ji.r(16, 5)]
    right[50].pitch.append(ji.r(1, 2))

    right[51].pitch = [ji.r(7, 3), ji.r(7, 4), ji.r(35, 12)]
    right[51].optional_some_pitches = None

    tw.change_octave(52, 1, right)
    right[52].pitch.append(ji.r(48, 35).register(1))
    tw.shorten(55, F(7, 16), right)

    tw.crop(45, right, F(1, 2), position=False)
    right[46].pitch = [ji.r(35, 24)]
    tw.crop(46, right, F(3, 8))
    tw.rest(47, right)

    tw.rest_many((59, 60, 61, 63), right)

    tw.crop(
        58,
        right,
        F(2, 4),
        F(2, 4),
        F(2, 4),
        F(2, 4),
        F(4, 4),
        F(1, 4),
        F(3, 4),
        F(4, 4),
    )
    right[58].pitch = [ji.r(48, 49).register(-1)]
    right[59].pitch = [ji.r(384, 245).register(-1)]
    right[60].pitch = [ji.r(8, 5)]
    right[61].pitch = [ji.r(256, 245)]
    right[62].pitch = [ji.r(48, 49).register(-1)]
    right[63].pitch = [ji.r(1, 1).register(-1)]
    right[64].pitch = [ji.r(7, 6).register(1)]
    right[65].pitch = [ji.r(4, 3).register(-1), ji.r(1, 2)]
    """

    """

    right[56].pitch = [ji.r(7, 3)]
    # tw.rest(57, right)
    # print("right", len(right))

    ###############################################
    #          left hand                          #
    ###############################################

    tw.crop(6, left, F(1, 8))
    tw.add_kenong(7, left)
    left[7].volume = 1
    left[16].arpeggio = attachments.Arpeggio(abjad.enums.Down)
    tw.rest_many((19, 20, 21, 22, 23, 24, 25, 26), left)

    for n in (17, 18):
        left[n].optional = None
        left[n].volume = 0.75

    tw.crop(19, left, *([F(1, 4)] * 9))

    current_idx = 19
    for n, pitch in ((4, ji.r(35, 24)), (3, ji.r(3, 2)), (2, ji.r(72, 49))):
        is_first = True
        for _ in range(n):
            if is_first:
                tw.add_gong(current_idx, left, pitch)
                is_first = False
            else:
                tw.add_kenong(current_idx, left, pitch)
                left[current_idx].volume = 1

            current_idx += 1

    left[30].arpeggio = attachments.Arpeggio(abjad.enums.Down)

    tw.rest_many((31, 32), left)
    tw.split(31, left, F(1, 4), F(1, 4))
    tw.add_kenong(31, left, ji.r(3, 2))
    tw.add_kenong(32, left, ji.r(35, 24))

    left[34].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    tw.rest_many((36, 38, 39, 40), left)
    tw.eat(35, 36, left)
    tw.eat(36, 37, left)
    tw.eat(36, 37, left)

    tw.eat(17, 18, left)
    tw.add_kenong(17, left, ji.r(288, 245))
    left[17].volume = 1.3

    # tw.make_solo_gong(36, left)
    tw.rest(36, left)
    left[37].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    left[39].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    tw.rest_many((38, 39), left)
    tw.eat(37, 38, left)
    tw.eat(38, 39, left)

    tw.rest(39, left)
    left[39].ottava = attachments.Ottava(0)
    left[39].pedal = attachments.Pedal(False)

    left[41].pedal = attachments.Pedal(True)
    left[42].arpeggio = attachments.Arpeggio(abjad.enums.Up)

    tw.make_solo_gong(44, left)
    tw.rest(43, left)
    tw.swap_duration(42, 43, F(1, 16), left)

    left[45].arpeggio = attachments.Arpeggio(abjad.enums.Up)

    left[58].optional = None
    left[58].volume = 0.75
    # tw.crop(59, left, F(1, 4), F(1, 4))
    tw.swap_duration(60, 59, F(1, 8), left)
    tw.add_gong(60, left, ji.r(72, 49))
    left[60].optional = None
    left[60].volume = 1

    tw.crop(42, left, F(1, 8))
    tw.add_kenong(43, left, ji.r(64, 63))
    left[43].volume = 1
    left[43].arpeggio = None
    left[44].ottava = attachments.Ottava(0)

    tw.swap_duration(48, 47, F(1, 8), left)
    tw.add_kenong(47, left, ji.r(64, 63))
    tw.add_kenong(48, left, ji.r(14, 9))
    left[47].volume = 1
    left[48].volume = 1
    tw.eat(48, 49, left)

    left[42].pitch = list(sorted(left[42].pitch)[:1])
    left[42].arpeggio = None

    tw.swap_duration(49, 50, F(2, 8), left)
    tw.add_kenong(50, left, ji.r(256, 245))
    left[50].volume = 1

    left[54].pitch = list(sorted(left[54].pitch)[:1])
    left[56].pitch = list(sorted(left[56].pitch)[:1])

    tw.rest(64, left)
    tw.swap_duration(64, 63, F(1, 4), left)
    # left[64].arpeggio = attachments.Arpeggio(abjad.enums.Down)
    left[64].arpeggio = None
    left[64].volume = 1

    tw.eat(62, 63, left)
    left[62].volume = 0.43
    tw.split(62, left, *([F(1, 4)] * int(left[62].delay // F(1, 4))))

    tw.split(60, left, F(3, 8), F(2, 8))
    left[61].ottava = attachments.Ottava(0)
    left[61].pedal = attachments.Pedal(False)
    left[61].volume = 0.5
    tw.split(61, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16))
    left[61].pitch = [ji.r(64, 63)]
    left[62].pitch = [ji.r(35, 32).register(0)]
    left[63].pitch = [ji.r(64, 63)]
    left[64].pitch = [ji.r(7, 9)]

    left[68].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    tw.eat(69, 70, left)

    tw.swap_duration(69, 70, F(1, 8), left)
    tw.add_kenong(70, left, ji.r(8, 5))

    left[78].volume = 0.5
    tw.crop(78, left, F(3, 16))
    left[80].volume = 0.5
    left[80].arpeggio = None
    tw.crop(80, left, F(1, 16), F(1, 16), F(1, 16))

    left[79].pitch = [ji.r(7, 9)]
    left[80].pitch = [ji.r(4, 7)]
    left[81].pitch = [ji.r(35, 24).register(-1)]
    tw.copy_pitch(80, 82, left)
    left[83].pitch = [ji.r(35, 32).register(0)]
    left[84].pitch = [ji.r(35, 24).register(-1)]

    tw.crop(84, left, F(1, 16), F(1, 16))
    left[85].pitch = [ji.r(4, 7).register(-1)]
    left[86].pitch = [ji.r(64, 63).register(-1)]

    tw.rest(83, left)
    tw.rest(86, left)

    tw.make_solo_gong(71, left)
    left[71].pedal = attachments.Pedal(True)

    tw.swap_duration(57, 58, F(1, 8), left)

    tw.rest_many((80, 81, 82, 84, 85, 87, 88, 89, 90, 91, 92, 93), left)

    tw.crop(80, left, F(1, 4), F(2, 4), F(2, 4), F(2, 4), F(3, 4), F(2, 4), F(3, 4))

    tw.add_kenong(80, left, ji.r(288, 245))
    tw.add_kenong(81, left, ji.r(384, 245))
    tw.add_kenong(82, left, ji.r(8, 5))
    tw.add_kenong(83, left, ji.r(256, 245))
    tw.add_kenong(84, left, ji.r(72, 49))
    tw.add_kenong(85, left, ji.r(7, 6))
    tw.add_kenong(86, left, ji.r(1, 1))
    tw.add_kenong(87, left, ji.r(1, 1))

    # for n in reversed(tuple(range(80, 87))):
    #     tw.crop(n, left, *([F(1, 8)] * int(left[n].delay // float(F(1, 8)))))

    tw.crop(75, left, F(1, 8))
    left[76].ottava = attachments.Ottava(0)
    left[76].pedal = attachments.Pedal(False)
    tw.crop(76, left, F(1, 16), F(3, 16), F(1, 8))
    left[76].pitch = [ji.r(1, 1)]
    left[77].pitch = [ji.r(7, 8)]
    left[78].pitch = [ji.r(7, 6)]
    left[79].pitch = [ji.r(4, 3)]
    left[80].pitch = [ji.r(72, 49)]
    # left[81].pitch = [ji.r(256, 245), ji.r(384, 245)]
    left[81].pitch = []
    left[81].volume = 0.65
    left[81].ottava = attachments.Ottava(0)
    left[82].pitch = [ji.r(288, 245)]
    tw.swap_duration(82, 83, F(1, 16), left)
    left[83].volume = 0.75
    left[83].pitch = [ji.r(256, 245)]

    tw.eat(83, 84, left)
    # tw.crop(83, left, F(1, 8))
    # left[84].pitch = [ji.r(144, 245), ji.r(24, 49)]
    tw.eat(80, 81, left)

    print("left", len(left))

    tw.crop(82, left, F(1, 8))
    tw.add_gong(83, left, ji.r(288, 245))

    # left[85].pedal = attachments.Pedal(True)

    tw.crop(90, left, F(6, 8))
    tw.add_gong(91, left, ji.r(14, 9))

    tw.swap_duration(80, 81, F(1, 8), left)
    tw.crop(81, left, F(1, 8))
    # tw.crop(83, left, F(1, 16))
    left[82].pitch = [ji.r(256, 245)]
    left[83].pitch = [ji.r(35, 48)]
    # left[84].pitch = [ji.r(288, 245).register(-1)]

    tw.crop(0, left, F(2, 8), F(1, 8))
    left[1].pitch = [ji.r(7, 24)]
    left[2].pitch = [ji.r(35, 128)]
    tw.crop(4, left, F(1, 4), F(1, 8), F(1, 8))
    left[5].pitch = [ji.r(12, 49)]
    left[6].pitch = [ji.r(96, 245)]
    left[7].pedal = attachments.Pedal(True)

    right[-1].fermata = attachments.Fermata("longfermata")
    left[-1].fermata = attachments.Fermata("longfermata")


def _adapt_left_hand(left: lily.NOventLine, vm) -> None:
    """left[79].pitch = [ji.r(48, 49).register(-2)]

    tw.crop(80, left, *([F(1, 16)] * 8))
    tw.eat(78, 79, left)

    pitches = (
        ji.r(384, 245).register(-2),
        ji.r(72, 49).register(-2),
        ji.r(288, 245).register(-1),
    )
    pitches += tuple(reversed(pitches))[1:]
    pitches = (ji.r(48, 49).register(-2),) + pitches
    pitches += (
        ji.r(48, 49).register(-2),
        ji.r(288, 245).register(-1),
    )

    for idx, p in enumerate(pitches):
        left[79 + idx].pitch = [p]
    """


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        "closing",
        tempo_factor=0.31,
        octave_of_first_pitch=-1,
        harmonic_tolerance=0.89,
        ro_temperature=0.685,
        ro_density=0.8,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.35, 0.1),
        area_density_reference_size=F(1, 2),
        area_min_split_size=F(1, 8),
    )

    vm.remove_area(0, 1)
    # vm.remove_area(30, len(vm.bars))
    # vm.remove_area(len(vm.bars) - 2, len(vm.bars) + 1)
    vm.add_bar(5, abjad.TimeSignature((3, 4)))
    vm.add_bar(9, abjad.TimeSignature((2, 4)))
    vm.add_bar(23, abjad.TimeSignature((1, 4)))
    vm.add_bar(25, abjad.TimeSignature((2, 4)))
    # vm.add_bar(26, abjad.TimeSignature((1, 4)))

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            tremolo_maker=infit.ActivityLevel(0),
            acciaccatura_maker=infit.ActivityLevel(5),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0)),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.7,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 16),
            optional_pitches_density=0.75,
            after_glissando_size=F(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(5),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 0, 0, 0)),
            harmonic_pitches_activity=0.4,
            harmonic_pitches_density=0.75,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 16),
            optional_pitches_density=0.75,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(0),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 0)),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(5),
            harmonic_pitches_activity=0.35,
            harmonic_pitches_density=0.7,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 16),
            optional_pitches_density=0.7,
            after_glissando_size=F(1, 8),
        ),
        keyboard=keyboard.KeyboardMaker(
            lh_min_volume=0.68,
            lh_max_volume=0.79,
            lh_min_metricity_to_add_harmony=0,
            lh_min_metricity_to_add_accent=10,
            lh_max_metricity_for_arpeggio=0.3,
            lh_min_metricity_to_add_restricted_harmony=0,
            lh_prohibit_repetitions=False,
            lh_add_repetitions_avoiding_notes=False,
            rh_likelihood_making_harmony=1,
            harmonies_max_difference=1200,
            harmonies_min_difference=250,
            colotomic_structure=(1, 2, 2, 2),
        ),
    )

    _adapt_violin(vm.violin.musdat[1], vm)
    _adapt_viola(vm.viola.musdat[1], vm)
    _adapt_cello(vm.cello.musdat[1], vm)
    _adapt_keyboard(vm.keyboard.musdat[2], vm.keyboard.musdat[1], vm)

    # vm.add_bar(33, abjad.TimeSignature((2, 4)), force_adding=True)

    # _adapt_left_hand(vm.keyboard.musdat[2], vm)

    for string in (vm.violin.musdat[1], vm.viola.musdat[1], vm.cello.musdat[1]):
        tw.detach_hauptstimme(string)
        tw.detach_optional_events(string)

    for instr in (
        vm.violin.musdat[1],
        vm.viola.musdat[1],
        vm.cello.musdat[1],
        vm.keyboard.musdat[2],
        vm.keyboard.musdat[1],
    ):
        tw.detach_optional_events(instr)

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

            """
            # adapting accidental notation of keyboard
            if instr == "keyboard" and idx[1] == 1:
                abjad.Accidental.respell_with_sharps(staff[6][3:])
                abjad.Accidental.respell_with_sharps(staff[7])
                abjad.Accidental.respell_with_sharps(staff[8])
                abjad.Accidental.respell_with_sharps(staff[18])
                abjad.Accidental.respell_with_sharps(staff[19])
                abjad.Accidental.respell_with_sharps(staff[20])
            """

            if instr == "violin":
                # abjad.attach(abjad.Dynamic('ppp'), staff[0][0])
                abjad.attach(abjad.StartHairpin(), staff[2][0])
                abjad.attach(abjad.Dynamic("p"), staff[3][0])
                abjad.attach(abjad.StartHairpin(">"), staff[3][6])
                abjad.attach(abjad.Dynamic("ppp"), staff[4][2])
                abjad.attach(abjad.StartHairpin(">"), staff[6][2])
                abjad.attach(abjad.Dynamic("pppp"), staff[7][0])
                # abjad.attach(
                #     abjad.StringContactPoint("sul tasto").markup, staff[7][0],
                # )
                # abjad.attach(
                #     abjad.StringContactPoint("ordinario").markup, staff[8][0],
                # )
                # abjad.attach(
                #     abjad.StringContactPoint("sul tasto").markup, staff[9][0],
                # )
                abjad.attach(abjad.Dynamic("pp"), staff[12][2])
                abjad.attach(abjad.Fermata(), staff[16][2])
                abjad.attach(abjad.Dynamic("p"), staff[17][0])
                abjad.attach(abjad.Dynamic("pppp"), staff[17][2])
                abjad.attach(abjad.StartHairpin(), staff[18][1])
                abjad.attach(abjad.Dynamic("p"), staff[19][0])
                abjad.attach(abjad.Dynamic("pp"), staff[22][-1])
                abjad.attach(abjad.Dynamic("p"), staff[30][2])
                abjad.attach(abjad.StartHairpin(">"), staff[31][-1])
                abjad.attach(abjad.Dynamic("pppp"), staff[33][0])
                # abjad.attach(FLAUTANDO, staff[33][0])

            elif instr == "viola":
                abjad.attach(abjad.StartHairpin(), staff[2][0])
                abjad.attach(abjad.Dynamic("pp"), staff[3][0])
                abjad.attach(abjad.StartHairpin(">"), staff[3][3])
                abjad.attach(abjad.Dynamic("ppp"), staff[4][1])
                abjad.attach(abjad.Dynamic("pppp"), staff[7][0])
                # abjad.attach(
                #     abjad.StringContactPoint("sul tasto").markup, staff[8][0],
                # )
                abjad.attach(abjad.Dynamic("pp"), staff[12][2])
                abjad.attach(abjad.Fermata(), staff[16][2])
                abjad.attach(abjad.Dynamic("p"), staff[17][0])
                abjad.attach(abjad.Dynamic("pp"), staff[18][2])
                abjad.attach(abjad.StartHairpin(), staff[18][2])
                abjad.attach(abjad.Dynamic("p"), staff[19][0])
                abjad.attach(abjad.Dynamic("pp"), staff[23][0])
                abjad.attach(abjad.Dynamic("p"), staff[30][1])
                abjad.attach(abjad.StartHairpin(">"), staff[31][-1])
                abjad.attach(abjad.Dynamic("pppp"), staff[33][0])
                # abjad.attach(FLAUTANDO, staff[33][0])

            elif instr == "cello":
                abjad.attach(abjad.StartHairpin(), staff[2][0])
                abjad.attach(abjad.Dynamic("pp"), staff[3][0])
                # abjad.attach(abjad.Dynamic('pp'), staff[2][0])
                abjad.attach(abjad.StartHairpin(">"), staff[3][5])
                abjad.attach(abjad.Dynamic("ppp"), staff[4][1])
                abjad.attach(abjad.StartHairpin(">"), staff[6][1])
                abjad.attach(abjad.Dynamic("pppp"), staff[7][0])
                abjad.attach(
                    abjad.StringContactPoint("sul tasto"), staff[8][0],
                )
                abjad.attach(abjad.Dynamic("pp"), staff[12][2])
                abjad.attach(abjad.Fermata(), staff[16][2])
                abjad.attach(abjad.Dynamic("p"), staff[17][0])
                abjad.attach(abjad.Dynamic("ppp"), staff[18][0])
                abjad.attach(abjad.StartHairpin(), staff[18][0])
                abjad.attach(abjad.Dynamic("p"), staff[19][0])
                abjad.attach(abjad.Dynamic("pp"), staff[23][0])
                abjad.attach(abjad.Dynamic("ppp"), staff[24][5])
                abjad.attach(abjad.Dynamic("pp"), staff[26][0])
                abjad.attach(abjad.Dynamic("ppp"), staff[29][0])
                abjad.attach(abjad.Dynamic("pp"), staff[29][4])
                abjad.attach(abjad.Dynamic("p"), staff[30][1])
                abjad.attach(abjad.StartHairpin(">"), staff[31][4])
                abjad.attach(abjad.Dynamic("pppp"), staff[33][0])

                # abjad.attach(FLAUTANDO, staff[33][0])

            elif instr == "keyboard":
                if idx[1] == 1:
                    abjad.attach(abjad.Dynamic("pp"), staff[2][0])
                    abjad.attach(abjad.Dynamic("ppp"), staff[7][0])
                    abjad.attach(abjad.Dynamic("p"), staff[11][0])
                    abjad.attach(abjad.Dynamic("pp"), staff[12][1])
                    abjad.attach(abjad.Dynamic("p"), staff[18][1])
                    abjad.attach(abjad.Dynamic("pp"), staff[26][3])
                    abjad.attach(abjad.Dynamic("ppp"), staff[27][1])
                    abjad.attach(abjad.Dynamic("pp"), staff[30][0])
                    abjad.attach(abjad.Dynamic("p"), staff[31][0])
                    abjad.attach(abjad.StartHairpin(">"), staff[32][1])
                    abjad.attach(abjad.Dynamic("ppp"), staff[33][0])

                    abjad.attach(abjad.Fermata(), staff[16][1])
                else:
                    abjad.attach(abjad.Fermata(), staff[16][1])

            abjad.attach(abjad.Dynamic("ppp"), staff[0][0])

    return verse
