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
    pass
    # violin[3].string_contact_point = attachments.StringContactPoint("pizzicato")
    # violin[3].volume = 2
    # tw.add_artifical_harmonic(3, violin[3].pitch[0], violin)
    # violin[3].pitch[0] += ji.r(4, 1)
    # tw.add_acciaccatura(
    #     3, ji.r(35, 32), violin, add_glissando=True, use_artifical_harmonic=True
    # )
    # violin[3].volume = 0.1
    tw.prolong(3, F(1, 8), violin)
    # tw.swap_duration(2, 3, F(1, 8), violin)
    previous_duration = F(violin[6].delay)
    # tw.split_by_structure(6, 2, violin, vm, adapt_by_changed_structure=True)
    tw.split(6, violin, F(3, 8), F(1, 4))
    violin[6].ornamentation = attachments.OrnamentationDown(1)
    violin[6].glissando = None
    difference = previous_duration - violin[7].duration
    violin[7].glissando.pitch_line[0].delay -= difference
    # tw.add_acciaccatura(10, ji.r(8, 9), violin, add_glissando=True)
    tw.swap_duration(11, 10, F(7, 32), violin)
    tw.add_acciaccatura(11, ji.r(8, 9), violin, add_glissando=True)
    violin[10].string_contact_point = attachments.StringContactPoint("arco")
    violin[11].string_contact_point = attachments.StringContactPoint("arco")
    violin[11].ornamentation = attachments.OrnamentationUp(1)
    tw.prolong(12, F(1, 8), violin)
    tw.split(12, violin, F(1, 8), F(1, 8))
    # tw.rest(10, violin)
    tw.prolong(8, F(1, 32), violin)
    tw.change_octave(17, -1, violin)
    # violin[17].tremolo = attachments.Tremolo()
    violin[17].volume = 0.5
    tw.add_glissando(
        17,
        (0, 0, 1),
        violin,
        # verse_maker=vm,
        # adapt_by_changed_structure=True,
        durations=(F(4, 16), F(3, 16)),
    )
    violin[19].acciaccatura = None
    tw.swap_duration(18, 19, F(1, 8), violin)
    # tw.split_by_structure(19, 2, violin, vm, adapt_by_changed_structure=True)
    tw.split(
        19, violin, F(1, 8), F(2, 8), F(3, 16),
    )
    tw.add_glissando(
        19,
        (-1, 0),
        violin,
        durations=(F(1, 8),),
        # verse_maker=vm,
        # adapt_by_changed_structure=True,
    )
    violin[20].ornamentation = attachments.OrnamentationUp(2)
    violin[21].ornamentation = attachments.OrnamentationUp(1)
    tw.add_acciaccatura(21, ji.r(3, 4), violin)
    violin[21].ornamentation = attachments.OrnamentationUp(1)
    violin[26].natural_harmonic = attachments.NaturalHarmonic()
    violin[26].string_contact_point = attachments.StringContactPoint("pizzicato")
    violin[26].volume = 1.3
    violin[28].acciaccatura.add_glissando = False
    tw.add_glissando(
        28,
        (0, 0, 2),
        violin,
        # verse_maker=vm,
        # adapt_by_changed_structure=True,
        durations=(F(1, 16), F(1, 8)),
    )
    violin[29].ornamentation = attachments.OrnamentationUp(1)

    tw.split(32, violin, F(1, 32), F(3, 16))
    violin[35].pitch = [violin[31].pitch[0].copy()]

    for n in (31, 32, 33, 34, 35):
        violin[n].string_contact_point = attachments.StringContactPoint("pizzicato")
        violin[n].volume = 0.95
        if n % 2 == 0:
            violin[n].natural_harmonic = attachments.NaturalHarmonic()
            tw.change_octave(n, 1, violin)
        else:
            tw.change_octave(n, -1, violin)

    tw.swap_duration(31, 32, F(1, 32), violin)
    # violin[36].string_contact_point = attachments.StringContactPoint("pizzicato")
    violin[36].string_contact_point = attachments.StringContactPoint("arco")
    violin[36].volume = 1
    violin[36].natural_harmonic = attachments.NaturalHarmonic()

    violin[39].ornamentation = attachments.OrnamentationDown(3)
    violin[41].hauptstimme = attachments.Hauptstimme(True, False)
    tw.split(
        42, violin, F(1, 32) + F(2, 4), F(1, 4) + F(1, 16),
    )
    violin[42].pitch = [violin[41].pitch[0].copy()]
    violin[42].hauptstimme = attachments.Hauptstimme(True, False)
    tw.split_by_structure(
        42, 3, violin, vm, adapt_by_changed_structure=True, set_n_novents2rest=0
    )
    violin[42].ornamentation = attachments.OrnamentationUp(1)
    violin[44].ornamentation = attachments.OrnamentationDown(1)
    violin[44].hauptstimme = attachments.Hauptstimme(False, False)
    violin[45].pitch = [ji.r(288, 245)]
    violin[45].volume = 0.6
    tw.split(45, violin, F(1, 8), F(3, 16))

    violin[47].hauptstimme = attachments.Hauptstimme(True, False)
    tw.split(48, violin, F(1, 4), F(3, 16))
    violin[48].hauptstimme = attachments.Hauptstimme(False, False)
    violin[48].pitch = [violin[47].pitch[0].copy()]
    violin[48].volume = 0.6
    violin[48].string_contact_point = attachments.StringContactPoint("arco")
    tw.split(48, violin, F(1, 8), F(1, 8))
    violin[49].acciaccatura = violin[41].acciaccatura
    # tw.split(51, violin, F(5, 8), F(2, 4))

    violin[51].optional = False
    violin[51].volume = 0.85
    violin[51].artifical_harmonic = None
    violin[51].pitch = [ji.r(28, 9)]
    tw.add_artifical_harmonic(51, ji.r(7, 9), violin)
    # violin[51].natural_harmonic = attachments.NaturalHarmonic()
    # tw.change_octave(51, -1, violin)
    tw.swap_duration(52, 51, F(7, 8), violin)
    tw.swap_duration(50, 51, F(3, 16), violin)
    tw.split_by_structure(50, 7, violin, vm, adapt_by_changed_structure=True)
    violin[50].pitch = [ji.r(6, 2)]
    violin[50].natural_harmonic = attachments.NaturalHarmonic()
    violin[50].artifical_harmonic = None
    tw.swap_duration(56, 55, F(1, 32), violin)

    # tw.change_octave(52, -1, violin)
    # violin[52].string_contact_point = attachments.StringContactPoint("pizzicato")
    # violin[52].volume = 1
    # violin[52].natural_harmonic = None

    # tw.rest(54, violin)

    tw.add_glissando(
        55, (0, 0, -1), violin, verse_maker=vm, adapt_by_changed_structure=True
    )

    violin[57].acciaccatura.add_glissando = False
    # tw.add_glissando(57, (0, 0,
    tw.prolong(57, F(1, 8), violin)

    tw.split_by_structure(57, 2, violin, vm, adapt_by_changed_structure=True)

    for n in (60, 61, 62):
        # violin[n].string_contact_point = attachments.StringContactPoint("arco")
        violin[n].string_contact_point = attachments.StringContactPoint("pizzicato")
        violin[n].artifical_harmonic = None
        # violin[n].volume = 0.5
        violin[n].volume = 1
        if n == 60:
            tw.change_octave(n, -2, violin)
        else:
            violin[n].natural_harmonic = attachments.NaturalHarmonic()
            tw.change_octave(n, -1, violin)

    # tw.swap_duration(64, 63, F(1, 8), violin)

    tw.split(56, violin, F(1, 8), F(1, 8))
    violin[57].pitch = [violin[58].pitch[0].copy()]
    violin[57].string_contact_point = attachments.StringContactPoint("arco")
    violin[57].volume = 0.54

    violin[70].acciaccatura = None
    violin[70].volume = 1
    violin[70].string_contact_point = attachments.StringContactPoint("pizzicato")
    tw.split_by_structure(70, 4, violin, vm, adapt_by_changed_structure=True)

    violin[71].string_contact_point = attachments.StringContactPoint("arco")
    violin[71].volume = 0.5

    # tw.split(74, violin, F(6, 4), F(2, 4))
    violin[74].pitch = [ji.r(288, 245)]
    violin[74].volume = 1
    violin[74].string_contact_point = attachments.StringContactPoint("pizzicato")
    tw.split_by_structure(74, 8, violin, vm, adapt_by_changed_structure=True)

    tw.swap_duration(72, 71, F(1, 32), violin)
    tw.add_glissando(
        71, (0, 0, -1), violin, durations=[F(3, 16), F(1, 16)],
    )


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    viola[1].string_contact_point = attachments.StringContactPoint("arco")
    tw.add_acciaccatura(3, ji.r(4, 3), viola, add_glissando=True)
    viola[7].acciaccatura = None
    viola[7].ornamentation = attachments.OrnamentationUp(2)
    tw.prolong(7, F(1, 16), viola)
    tw.add_glissando(
        7, (0, 0, -1), viola, durations=(F(3, 8), F(1, 8)),
    )
    tw.change_octave(10, -1, viola)
    viola[14].pitch = [viola[13].pitch[0].copy()]
    viola[14].string_contact_point = attachments.StringContactPoint("arco")
    viola[14].ornamentation = attachments.OrnamentationUp(1)
    tw.split_by_structure(14, 2, viola, vm)
    tw.rest(14, viola)
    # viola[14].articulation_once = attachments.ArticulationOnce(".")
    tw.change_octave(19, 1, viola)

    # tw.split(22, viola, F(3, 8), F(1, 8))
    viola[22].glissando = None
    tw.add_acciaccatura(22, ji.r(35, 24), viola, add_glissando=False)
    tw.add_glissando(
        22, (0, 0, -1), viola, durations=(F(1, 4), F(1, 8)),
    )
    tw.add_glissando(
        24, (0, -1), viola, verse_maker=vm, adapt_by_changed_structure=True
    )
    viola[22].hauptstimme = attachments.Hauptstimme(True, False)
    viola[24].hauptstimme = attachments.Hauptstimme(False, False)
    viola[26].pitch = [viola[25].pitch[0].copy()]
    viola[26].ornamentation = attachments.OrnamentationDown(1)
    tw.add_acciaccatura(26, ji.r(8, 5), viola)
    viola[26].optional = None
    viola[26].volume = 0.7
    # tw.swap_duration(26, 25, F(1, 4), viola)
    # tw.split(
    #     21,
    #     viola,
    #     F(1, 8),
    #     F(1, 2),
    #     F(1, 8),
    # )
    # viola[23].tempo = attachments.Tempo(F(1, 4), 30)
    # viola[25].tempo = attachments.Tempo(F(1, 4), 40)
    # viola[34].string_contact_point = attachments.StringContactPoint("pizzicato")
    # viola[34].volume = 1.3
    tw.swap_duration(35, 34, F(1, 8), viola)
    viola[34].ornamentation = attachments.OrnamentationUp(1)
    tw.swap_duration(36, 35, F(1, 4), viola)
    tw.split(
        35, viola, F(1, 8), F(1, 8), F(1, 4),
    )
    viola[35].string_contact_point = attachments.StringContactPoint("pizzicato")
    viola[35].volume = 1
    viola[36].string_contact_point = attachments.StringContactPoint("pizzicato")
    viola[36].volume = 1
    viola[37].ornamentation = attachments.OrnamentationDown(1)
    viola[40].string_contact_point = attachments.StringContactPoint("pizzicato")
    viola[40].volume = 1.2
    viola[40].optional = None
    tw.swap_duration(41, 40, F(1, 8), viola)
    tw.split(
        40, viola, F(1, 8), F(1, 8),
    )
    tw.change_octave(41, 1, viola)
    # viola[41].prall = attachments.Prall()
    viola[43].string_contact_point = attachments.StringContactPoint("pizzicato")
    # viola[43].prall = attachments.Prall()
    viola[43].volume = 1.2
    # tw.swap_duration(44, 45, F(1, 8), viola)
    # tw.split(44, viola, F(1, 4), F(1, 8))
    tw.split(45, viola, F(1, 8), F(1, 8))
    # tw.add_glissando(
    #     44,
    #     (-1, 0, 0),
    #     viola,
    #     durations=[F(1, 8), F(1, 8)],
    # )
    viola[45].ornamentation = attachments.OrnamentationUp(1)
    viola[46].ornamentation = attachments.OrnamentationDown(1)
    viola[48].ornamentation = attachments.OrnamentationUp(2)
    tw.split(
        49, viola, F(1, 8), F(1, 8), F(1, 8),
    )
    viola[50].ornamentation = attachments.OrnamentationDown(1)
    viola[51].ornamentation = attachments.OrnamentationUp(1)
    # viola[55].tremolo = attachments.Tremolo()
    viola[55].volume = 0.6
    tw.split(58, viola, F(1, 4), F(1, 2))
    viola.insert(59, viola[60].copy())
    viola[60].duration = F(1, 4)
    viola[60].delay = F(1, 4)
    viola[59].hauptstimme = attachments.Hauptstimme(True, False)
    tw.add_acciaccatura(59, ji.r(7, 4), viola, add_glissando=True)
    tw.add_acciaccatura(61, ji.r(7, 4), viola, add_glissando=False)
    viola[62].artifical_harmonic = None
    viola[62].volume = 0.8
    tw.change_octave(62, -1, viola)
    viola[62].string_contact_point = attachments.StringContactPoint("arco")
    viola[62].optional = None
    tw.prolong(62, F(1, 8), viola)
    viola[63].artifical_harmonic = None
    tw.change_octave(63, -1, viola)
    viola[64].volume = 0.8
    viola[64].optional = None
    viola[64].artifical_harmonic = None
    tw.change_octave(64, -1, viola)

    tw.add_glissando(
        61, (0, 0, -1), viola, durations=(F(3, 16), F(1, 16)),
    )
    tw.add_glissando(
        62, (0, 0, -1), viola, durations=(F(3, 16), F(1, 16)),
    )
    tw.add_glissando(
        63, (0, 0, 2), viola, durations=(F(3, 16), F(1, 16)),
    )
    viola[64].ornamentation = attachments.OrnamentationDown(1)

    viola[68].pitch = [viola[67].pitch[0].copy()]
    for n in (66, 67, 68, 69, 70, 71):
        viola[n].artifical_harmonic = None
        tw.change_octave(n, -1, viola)
        viola[n].string_contact_point = attachments.StringContactPoint("arco")
        viola[n].volume = 0.75

    tw.split_by_structure(73, 2, viola, vm, adapt_by_changed_structure=True)
    viola[73].hauptstimme = attachments.Hauptstimme(True, False)
    viola[74].hauptstimme = attachments.Hauptstimme(False, False)
    tw.add_acciaccatura(
        73, ji.r(4, 7), viola, add_glissando=True, use_artifical_harmonic=True
    )
    tw.split(
        75, viola, F(1, 16), F(1, 8), F(1, 4),
    )
    viola[76].pitch = [viola[68].pitch[0].copy().register(0)]
    viola[76].string_contact_point = attachments.StringContactPoint("arco")
    viola[76].volume = 0.6
    viola[77].pitch = [viola[76].pitch[0].copy().register(0)]
    viola[77].string_contact_point = attachments.StringContactPoint("arco")
    viola[77].volume = 0.6
    tw.split(77, viola, F(1, 8), F(1, 8))
    tw.add_glissando(78, (0, 1), viola, durations=[F(1, 8)])

    for n in (79, 81, 82, 83):
        viola[n].volume = 0.6
        viola[n].string_contact_point = attachments.StringContactPoint("arco")

    tw.swap_duration(84, 83, F(5, 8), viola)
    for n in (81, 82, 83):
        tw.change_octave(n, 1, viola)
        tw.add_artifical_harmonic(n, ji.r(2, 3), viola)

    tw.add_acciaccatura(83, ji.r(7, 8), viola, use_artifical_harmonic=True)
    # viola[83].acciaccatura = None
    tw.split_by_structure(83, 6, viola, vm, adapt_by_changed_structure=True)
    tw.swap_duration(88, 87, F(1, 8), viola)

    viola[84].acciaccatura = None
    viola[85].acciaccatura = None
    viola[86].acciaccatura = None
    viola[87].acciaccatura = None

    # viola[85].pitch = [ji.r(7, 4)]
    for n in (85,):
        viola[n].pitch = [ji.r(7, 2)]
        tw.add_artifical_harmonic(n, ji.r(7, 8), viola)

    viola[87].pitch = [ji.r(4, 3)]
    viola[87].artifical_harmonic = None

    tw.add_glissando(
        87, (0, 0, -1), viola, durations=[F(3, 16), F(1, 16)],
    )

    viola[90].artifical_harmonic = None
    viola[90].ornamentation = attachments.OrnamentationDown(2)

    tw.add_acciaccatura(92, ji.r(2, 3), viola, use_artifical_harmonic=True)
    tw.shorten(92, F(1, 8), viola)

    tw.change_octave(94, -1, viola)
    tw.prolong(94, F(1, 8), viola)
    viola[94].string_contact_point = attachments.StringContactPoint("arco")
    viola[94].volume = 0.7
    viola[94].optional = None
    tw.add_glissando(
        94, (0, 0, 1), viola, durations=[F(3, 16), F(1, 16)],
    )
    viola[95].ornamentation = attachments.OrnamentationUp(1)
    viola[95].volume = 0.7
    viola[95].string_contact_point = attachments.StringContactPoint("arco")
    tw.change_octave(95, -2, viola)
    viola[95].artifical_harmonic = None
    viola[95].optional = None
    tw.prolong(95, F(1, 8), viola)

    tw.split(
        88, viola, F(1, 8), F(1, 8), F(1, 4),
    )

    viola[89].pitch = [ji.r(48, 49)]
    viola[89].volume = 0.88
    viola[89].string_contact_point = attachments.StringContactPoint("arco")

    viola[90].pitch = [ji.r(48, 49)]
    viola[90].volume = 0.94
    viola[90].string_contact_point = attachments.StringContactPoint("arco")

    # tw.split(89, viola, F(1, 8), F(1, 8))
    viola[100].acciaccatura = None
    tw.add_glissando(
        100, (0, -2), viola, verse_maker=vm, adapt_by_changed_structure=True
    )
    tw.add_glissando(
        103, (-2, 0, 0), viola, verse_maker=vm, adapt_by_changed_structure=True
    )

    tw.rest(101, viola)

    viola[122].pitch = [viola[121].pitch[0].copy()]

    for n in (107, 109, 110, 111, 113, 114, 115, 116, 117, 119, 120, 121, 122):
        # viola[n].acciaccatura = None
        viola[n].volume = 1.1
        viola[n].string_contact_point = attachments.StringContactPoint("pizzicato")

    tw.split_by_structure(122, 5, viola, vm, adapt_by_changed_structure=True)


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    pass
    # tw.add_glissando(4, (0, 0, 1), cello, verse_maker=vm)
    # cello[3].acciaccatura = None
    cello[3].acciaccatura.add_glissando = True
    tw.add_acciaccatura(4, ji.r(8, 15), cello, add_glissando=True)
    tw.split_by_structure(5, 2, cello, verse_maker=vm)
    tw.rest(5, cello)
    # tw.add_acciaccatura(6, ji.r(6, 7), cello, add_glissando=True)
    tw.prolong(6, F(1, 32), cello)
    cello[8].string_contact_point = attachments.StringContactPoint("pizzicato")
    # cello[8].bartok_pizzicato = attachments.BartokPizzicato()
    cello[8].optional = False
    cello[8].volume = 1.35
    cello[14].string_contact_point = attachments.StringContactPoint("arco")
    cello[14].volume = 0.7

    for n in (10, 11, 13, 14):
        cello[n].artifical_harmonic = None
        cello[n].acciaccatura = None
        cello[n].pitch[0] -= ji.r(2, 1)

    # cello[14].string_contact_point = attachments.StringContactPoint("pizzicato")
    # cello[14].prall = attachments.Prall()
    tw.prolong(8, F(5, 16), cello)
    tw.split_by_structure(8, 2, cello, verse_maker=vm)
    cello[8].prall = attachments.Prall()
    cello[21].acciaccatura = None
    cello[21].ornamentation = attachments.OrnamentationDown(1)
    cello[23].natural_harmonic = attachments.NaturalHarmonic()
    cello[23].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[23].volume = 1.2
    tw.change_octave(23, -1, cello)
    cello[26].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[26].volume = 1.2
    tw.split_by_structure(
        25, 2, cello, verse_maker=vm, adapt_by_changed_structure=False
    )
    cello[25].hauptstimme = attachments.Hauptstimme(True, False)
    cello[26].hauptstimme = attachments.Hauptstimme(False, False)
    tw.add_acciaccatura(
        26,
        ji.r(12, 7).register(-2),
        cello,
        use_artifical_harmonic=True,
        add_glissando=False,
    )
    cello[26].ornamentation = attachments.OrnamentationUp(3)
    cello[29].optional = None
    tw.swap_duration(30, 29, F(10, 32), cello)
    # cello[28].volume = 0.4
    # cello[28].string_contact_point = attachments.StringContactPoint("arco")
    cello[29].volume = 0.8
    tw.split(29, cello, *([F(1, 8)] * 4))
    cello[30].natural_harmonic = attachments.NaturalHarmonic()
    tw.change_octave(31, -1, cello)
    tw.swap_duration(32, 31, F(1, 8), cello)
    tw.rest(29, cello)
    # tw.split(28, cello, F(1, 2), F(1, 8))
    # cello[29].tempo = attachments.Tempo(F(1, 4), 30)
    # cello[32].tempo = attachments.Tempo(F(1, 4), 40)
    # cello[28].tremolo = attachments.Tremolo()
    cello[34].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[34].volume = 1.2
    # cello[36].string_contact_point = attachments.StringContactPoint("pizzicato")
    # cello[36].volume = 0.8
    cello[36].artifical_harmonic = None
    tw.change_octave(36, -2, cello)
    tw.swap_duration(37, 36, F(5, 32), cello)
    cello[37].artifical_harmonic = None
    tw.change_octave(37, -1, cello)
    tw.add_glissando(
        37, (-1, 0, 0), cello, durations=[F(1, 32), F(5, 16)],
    )
    cello[39].artifical_harmonic = None
    tw.change_octave(39, -1, cello)
    tw.swap_duration(38, 39, F(1, 16), cello)
    tw.add_glissando(
        39, (-1, 0, 0, -1), cello, durations=[F(1, 16), F(4, 16), F(1, 16)],
    )
    cello[41].string_contact_point = attachments.StringContactPoint("pizzicato")
    tw.change_octave(41, -1, cello)
    cello[43].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[43].acciaccatura = None
    cello[43].volume = 0.9
    # cello[43].prall = attachments.Prall()
    tw.swap_duration(42, 43, F(3, 32), cello)
    # cello[50].volume = 0.36
    # cello[50].tremolo = attachments.Tremolo()
    # tw.swap_duration(51, 50, F(5, 32), cello)
    cello[51].volume = 0.6
    # cello[51].tremolo = attachments.Tremolo()
    cello[51].string_contact_point = attachments.StringContactPoint("arco")
    tw.shorten(55, F(1, 4), cello)
    cello[57].artifical_harmonic = None
    tw.change_octave(57, -1, cello)
    tw.prolong(57, F(5, 32), cello)
    tw.add_glissando(
        57, (0, 0, -1), cello, durations=[F(3, 16), F(1, 16)],
    )
    # cello[58].glissando = None
    cello[59].acciaccatura = None
    cello[59].ornamentation = attachments.OrnamentationUp(1)
    cello[61].ornamentation = attachments.OrnamentationUp(2)
    cello[63].string_contact_point = attachments.StringContactPoint("arco")
    tw.shorten(63, F(1, 32), cello)
    tw.add_glissando(
        63, (-1, 0, 0, -1), cello, durations=[F(1, 16), F(3, 16), F(1, 16)],
    )

    cello[70].glissando = None
    tw.split(70, cello, F(3, 16), F(1, 16))

    tw.prolong(72, F(9, 16), cello)
    tw.split_by_structure(72, 8, cello, vm, adapt_by_changed_structure=True)
    tw.swap_duration(79, 78, F(1, 16), cello)

    cello[73].ornamentation = attachments.OrnamentationDown(1)
    cello[75].ornamentation = attachments.OrnamentationUp(1)
    cello[77].ornamentation = attachments.OrnamentationDown(1)
    tw.add_glissando(
        78, (0, 0, -1), cello, durations=[F(3, 16), F(1, 16)],
    )

    tw.swap_duration(79, 80, F(1, 4), cello)
    cello[80].optional = False
    cello[80].volume = 0.5
    tw.prolong(80, F(1, 16), cello)
    tw.add_glissando(
        80,
        (-1, -1, 0, 0, -1),
        cello,
        durations=[F(1, 8), F(1, 16), F(4, 16), F(1, 16)],
    )

    cello[84].glissando = None
    tw.split(
        84, cello, F(1, 4), F(1, 8), F(1, 8),
    )
    tw.rest(85, cello)
    tw.add_glissando(86, (0, -1), cello, durations=[F(1, 8)])
    tw.add_acciaccatura(
        84, ji.r(8, 15), cello, use_artifical_harmonic=True, add_glissando=True
    )
    cello[84].ornamentation = attachments.OrnamentationDown(1)

    tw.split(
        87, cello, F(1, 8), F(1, 8),
    )

    tw.split_by_structure(82, 3, cello, vm, adapt_by_changed_structure=True)

    [tw.rest(91, cello) for _ in range(2)]
    for n in (91, 92):
        cello[n].volume = 0.66
        cello[n].string_contact_point = attachments.StringContactPoint("arco")

    for n in (96, 98):
        cello[n].artifical_harmonic = None
        cello[n].volume = 1
        cello[n].string_contact_point = attachments.StringContactPoint("pizzicato")
        tw.change_octave(n, -1, cello)

    tw.prolong(98, F(2, 4), cello)
    tw.split_by_structure(98, 9, cello, vm, adapt_by_changed_structure=True)

    cello[94].volume = 1
    cello[94].string_contact_point = attachments.StringContactPoint("pizzicato")
    tw.prolong(94, F(5, 16), cello)
    tw.split_by_structure(94, 4, cello, vm, adapt_by_changed_structure=True)
    cello[94].volume = 0.6
    cello[94].optional = None
    cello[94].string_contact_point = attachments.StringContactPoint("arco")


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine, vm) -> None:
    pass

    ########################################################
    #                   right hand                         #
    ########################################################

    tw.shorten(9, F(3, 16), right)
    tw.rest(11, right)
    right[22].pitch = [right[21].pitch[0].copy()]
    right[20].pitch = [right[19].pitch[0].copy()]
    # right[21].tempo = attachments.Tempo(F(1, 4), 30)
    tw.split(
        22, right, F(1, 8), F(1, 8), F(2, 8),
    )
    tw.rest(23, right)
    # right[23].tempo = attachments.Tempo(F(1, 4), 40)
    tw.split_by_structure(
        28, 5, right, vm, adapt_by_changed_structure=True, set_n_novents2rest=2
    )
    tw.swap_duration(37, 38, F(5, 16), right)
    tw.split(38, right, F(1, 8), F(3, 8))

    tw.split_by_structure(46, 5, right, vm, adapt_by_changed_structure=True)
    tw.prolong(
        67, F(1, 32) + F(1, 8) + F(2, 4), right,
    )
    # tw.rest(76, right)

    ########################################################
    #                   left hand                          #
    ########################################################

    tw.split(5, left, F(1, 16), F(1, 4))
    tw.rest(10, left)
    for n in (21, 20, 19):
        tw.rest(n, left)

    tw.prolong(18, F(1, 4), left)
    tw.swap_duration(18, 19, F(1, 32), left)
    tw.make_solo_gong(20, left)
    for n in (39, 38, 37, 36):
        tw.rest(n, left)

    # left[35].tempo = attachments.Tempo(F(1, 4), 30)
    # left[36].tempo = attachments.Tempo(F(1, 4), 40)

    tw.make_solo_gong(35, left)
    tw.swap_duration(36, 35, F(5, 16), left)

    tw.rest(48, left)
    tw.shorten(50, F(7, 16), left)

    left[51].pitch = [ji.r(288, 245).register(keyboard.SYMBOLIC_GONG_OCTAVE)]
    left[51].ottava = attachments.Ottava(-1)
    left[51].pedal = attachments.Pedal(True)
    tw.swap_duration(52, 51, F(1, 16), left)
    tw.rest(56, left)
    tw.rest(55, left)
    left[69].optional = None
    del left[70]
    left.insert(70, left[70].copy())
    # left.insert(70, left[70].copy())
    left.insert(71, left[67].copy())
    left.insert(72, left[68].copy())
    left.insert(73, left[69].copy())

    for n in (61, 59, 58, 57):
        tw.rest(n, left)

    tw.swap_duration(72, 71, F(1, 4), left)
    left[73].choose = None

    for n in (77, 76):
        tw.rest(n, left)

    tw.make_solo_gong(77, left)

    for n in (90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78):
        tw.rest(n, left)

    left[78].ottava = attachments.Ottava(0)
    tw.swap_duration(78, 77, F(1, 4), left)
    tw.split(
        78, left, F(3, 4), F(3, 4), F(2, 4), F(2, 4),
    )

    left[79].pitch = [ji.r(1, 1).register(keyboard.SYMBOLIC_GONG_OCTAVE)]
    left[79].ottava = attachments.Ottava(-1)
    left[79].pedal = attachments.Pedal(True)

    left[80].ottava = attachments.Ottava(0)

    # tw.swap_duration(83, 84, F(2, 4), left)
    # left[84].pitch = [ji.r(1, 1).register(keyboard.SYMBOLIC_GONG_OCTAVE)]
    left[81].pitch = [ji.r(14, 9).register(keyboard.SYMBOLIC_GONG_OCTAVE)]
    # left[84].ottava = attachments.Ottava(-1)
    left[81].ottava = attachments.Ottava(-1)
    left[81].pedal = attachments.Pedal(True)
    # tw.split(81, left, F(3, 8), F(1, 8))

    # left[82].ottava = attachments.Ottava(0)
    # left[82].pitch = [left[83].pitch[0].copy()]
    left[82].pitch.append(left[84].pitch[0].copy())
    left[82].arpeggio = attachments.Arpeggio(abjad.enums.Up)

    for n in (96, 95, 94, 93):
        tw.rest(n, left)


#####################################################
#            post processing functions2             #
#####################################################


def _adapt_violin2(violin: lily.NOventLine, vm) -> None:
    tw.crop(3, violin, F(1, 8))
    violin[4].pitch = [ji.r(35, 32)]
    tw.prolong(4, F(1, 8), violin)
    tw.crop(4, violin, F(1, 8))
    violin[5].pitch = [ji.r(7, 9)]
    violin[5].volume = 0.23

    tw.crop(1, violin, F(1, 4))
    violin[2].pitch = [ji.r(48, 35)]
    violin[2].acciaccatura = None
    violin[3].pitch = [ji.r(288, 245)]
    tw.set_arco(3, violin)
    # tw.shorten(3, F(1, 16), violin)
    tw.crop(3, violin, F(1, 16))
    violin[4].pitch = [ji.r(48, 35)]
    violin[4].volume = 0.4

    violin[8].pitch = [ji.r(35, 32)]
    tw.shorten(8, F(4, 4) + F(1, 16), violin)
    tw.set_pizz(8, violin)

    tw.crop(8, violin, F(2, 4))
    tw.crop(10, violin, F(3, 8), F(1, 8), F(1, 8), F(1, 16), F(1, 16), F(1, 8), F(1, 8))
    violin[11].pitch = [ji.r(8, 9)]
    violin[13].pitch = [ji.r(8, 9)]
    violin[14].pitch = [ji.r(48, 35)]
    violin[15].pitch = [ji.r(16, 9)]
    violin[16].pitch = [ji.r(14, 9)]
    for n in range(11, 17):
        tw.set_arco(n, violin)

    tw.rest(12, violin)

    tw.crop(19, violin, F(1, 4), F(1, 8))
    violin[20].ornamentation = None
    violin[20].pitch = [ji.r(48, 35)]
    tw.crop(21, violin, F(1, 8))
    tw.set_pizz(20, violin)
    tw.set_pizz(21, violin)
    violin[21].glissando = None
    violin[22].glissando = None

    tw.postpone(23, F(1, 8), violin)
    # tw.prolong(24, F(1, 8), violin)

    tw.crop(23, violin, F(1, 16))
    violin[24].pitch = [ji.r(8, 9)]
    tw.set_arco(24, violin)

    tw.crop(26, violin, F(1, 16), F(1, 16))
    violin[26].pitch = [ji.r(8, 9)]
    tw.set_arco(26, violin)
    violin[27].pitch = [ji.r(3, 2)]
    tw.set_arco(27, violin)

    tw.rest(29, violin)

    tw.crop(28, violin, F(1, 8), F(1, 16), F(1, 16))
    violin[28].pitch = [ji.r(288, 245)]
    violin[29].pitch = [ji.r(3, 2)]
    violin[30].pitch = [ji.r(14, 9)]

    for n in range(28, 31):
        tw.set_arco(n, violin)

    tw.rest(32, violin)
    tw.crop(31, violin, F(1, 16), F(3, 16), F(4, 16))
    violin[32].pitch = [ji.r(3, 4)]
    # violin[31].pitch = [ji.r(3, 2)]
    # violin[32].pitch = [ji.r(288, 245)]
    # tw.set_arco(31, violin)
    tw.set_arco(32, violin)

    violin[34].pitch = [ji.r(48, 35)]
    tw.set_arco(34, violin)

    tw.crop(36, violin, F(1, 8))
    violin[36].pitch = [ji.r(48, 35)]
    tw.set_arco(36, violin)

    tw.set_pizz(36, violin)
    tw.postpone(36, F(1, 16), violin)

    tw.crop(38, violin, F(1, 16), F(1, 16), F(1, 4))
    violin[39].pitch = [ji.r(288, 245)]
    violin[40].pitch = [ji.r(3, 4)]

    for n in (39, 40):
        tw.set_pizz(n, violin)

    tw.crop(41, violin, F(1, 4))
    violin[42].pitch = [ji.r(35, 32)]
    tw.set_arco(42, violin)

    violin[43].pitch = [ji.r(288, 245)]

    tw.crop(44, violin, F(3, 8))
    violin[44].pitch = [ji.r(288, 245).register(0)]
    tw.set_arco(44, violin)

    tw.crop(43, violin, F(1, 16))
    violin[44].pitch = [ji.r(48, 35).register(0)]

    # for n in (42, 43, 44, 45):
    #     tw.change_octave(n, 1, violin)

    tw.crop(45, violin, F(1, 8))
    tw.copy_pitch(44, 46, violin)

    tw.crop(46, violin, F(1, 8), F(1, 16))
    violin[48].pitch = [ji.r(16, 9)]
    tw.rest(47, violin)

    tw.crop(49, violin, F(1, 8))
    violin[49].pitch = [ji.r(48, 35)]
    tw.set_arco(49, violin)

    tw.crop(42, violin, F(1, 8))
    tw.rest(43, violin)

    violin[52].glissando = None
    tw.shorten(53, F(1, 8), violin)
    tw.set_pizz(52, violin)
    tw.set_pizz(53, violin)
    tw.set_pizz(54, violin)

    violin[52].pitch = [ji.r(3, 2)]
    violin[53].ornamentation = None
    violin[55].ornamentation = None

    tw.eat(55, 54, violin)
    tw.shorten(54, F(1, 16), violin)
    tw.set_pizz(54, violin)
    tw.change_octave(54, -1, violin)
    violin[54].acciaccatura = None

    tw.eat(56, 55, violin)
    tw.eat(55, 56, violin)

    tw.set_pizz(55, violin)
    tw.change_octave(55, 1, violin)

    tw.set_pizz(56, violin)
    tw.change_octave(56, 1, violin)
    violin[56].acciaccatura = None

    tw.crop(59, violin, F(1, 4))
    violin[60].pitch = [ji.r(288, 245)]
    tw.set_pizz(60, violin)

    tw.crop(62, violin, F(1, 8))
    violin[63].ornamentation = None
    # tw.change_octave(63, -1, violin)

    # for n in (50, 49, 47, 46, 45, 44, 42):
    #     tw.set_pizz(n, violin)
    for n in (49, 44):
        tw.set_pizz(n, violin)

    tw.crop(63, violin, F(1, 8))
    tw.set_arco(64, violin)
    violin[64].pitch = [ji.r(48, 35)]
    violin[64].volume = 0.34

    tw.eat(62, 63, violin)

    tw.swap_duration(63, 62, F(1, 16), violin)

    tw.crop(63, violin, F(3, 16))
    violin[64].pitch = [ji.r(7, 9)]

    tw.eat(64, 65, violin)
    tw.eat(64, 65, violin)

    tw.crop(64, violin, F(1, 4))
    violin[65].pitch = [ji.r(3, 4)]
    tw.eat(65, 66, violin)

    # tw.shorten(63, F(1, 16), violin)
    # tw.crop(63, violin, F(1, 16), F(1, 16), position=False)
    # tw.rest(64, violin)

    tw.add_glissando(62, (0, 0, -1), violin, durations=[F(4, 16), F(1, 16)])
    tw.swap_duration(64, 65, F(1, 16), violin)
    tw.crop(65, violin, F(3, 16))
    tw.set_pizz(66, violin)
    # [tw.eat(66, 67, violin) for _ in range(3)]
    tw.rest_many((67, 68, 69), violin)

    tw.postpone(66, F(1, 16), violin)
    # tw.swap_duration(66, 65, F(1, 16), violin)
    tw.change_octave(67, 1, violin)

    tw.crop(68, violin, F(1, 16), F(1, 4))
    violin[68].pitch = [ji.r(16, 9)]
    violin[69].pitch = [ji.r(128, 63)]

    tw.set_pizz(68, violin)
    tw.set_pizz(69, violin)

    tw.postpone(60, F(1, 16), violin)

    tw.change_octave(32, 1, violin)
    violin[32].natural_harmonic = attachments.NaturalHarmonic()

    tw.crop(69, violin, F(3, 16))
    tw.crop(
        71,
        violin,
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 8),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 8),
        F(1, 16),
    )

    violin[70].pitch = [ji.r(3, 1)]
    violin[72].pitch = [ji.r(48 * 2, 35)]
    violin[73].pitch = [ji.r(3, 1)]
    violin[74].pitch = [ji.r(28, 9)]
    violin[75].pitch = [ji.r(64, 63).register(2)]
    violin[76].pitch = [ji.r(3, 2).register(1)]
    violin[77].pitch = [ji.r(48, 35).register(1)]
    violin[79].pitch = [ji.r(3, 2).register(1)]
    violin[80].pitch = [ji.r(64, 63).register(1)]
    violin[81].pitch = [ji.r(3, 2).register(1)]
    violin[82].pitch = [ji.r(14, 9).register(1)]
    # violin[83].pitch = [ji.r(1, 1).register(2)]
    violin[84].pitch = [ji.r(64, 63).register(2)]
    violin[85].pitch = [ji.r(3, 2).register(1)]
    violin[86].pitch = [ji.r(48, 35).register(1)]
    violin[87].pitch = [ji.r(16, 9).register(1)]
    violin[88].pitch = [ji.r(3, 2).register(1)]
    violin[89].pitch = [ji.r(64, 63).register(1)]
    violin[90].pitch = [ji.r(3, 2).register(1)]
    violin[92].pitch = [ji.r(16, 9).register(1)]
    violin[93].pitch = [ji.r(3, 2).register(1)]

    [tw.set_arco(n, violin) for n in range(70, 94)]
    [tw.set_arco(idx + 94, violin) for idx, ev in enumerate(violin[94:])]

    # tw.change_octave(94, 1, violin)
    for n in range(70, 94):
        tw.change_octave(n, -1, violin)
        tw.set_pizz(n, violin)
        violin[n].volume = 0.95

    # tw.swap_duration(94, 95, F(1, 32), violin)
    # violin[95].ornamentation = None
    # tw.crop(95, violin, F(1, 16), F(1, 16))
    # violin[95].pitch = [ji.r(3, 2).register(1)]
    # violin[95].acciaccatura = None
    # violin[96].acciaccatura = None
    # violin[96].pitch = [ji.r(48, 35).register(1)]

    # violin[97].ornamentation = None

    # tw.change_octave(84, -1, violin)
    # tw.eat(84, 85, violin)
    # tw.copy_pitch(84, 85, violin)
    # tw.change_octave(86, -1, violin)

    # [tw.eat(91, 92, violin) for _ in range(2)]
    # tw.eat(89, 90, violin)
    # violin[90].pitch = [ji.r(288, 245).register(1)]
    # tw.add_glissando(90, (0, -2), violin)

    tw.rest_many(tuple(range(94, 101)), violin)

    # tw.crop(94, violin, F(3, 8))
    # violin[94].pitch = [ji.r(14, 9).register(-1)]
    # tw.set_arco(94, violin)
    # violin[94].volume = 0.3
    # tw.postpone(94, F(1, 8), violin)

    tw.crop(94, violin, *([F(1, 8)] * 8))
    violin[94].pitch = [ji.r(64, 63)]
    violin[95].pitch = [ji.r(3, 2)]
    violin[96].pitch = [ji.r(35, 32)]
    violin[97].pitch = [ji.r(3, 4)]
    violin[98].pitch = [ji.r(7, 9)]
    violin[99].pitch = [ji.r(8, 9)]

    for n in range(94, 100):
        tw.set_pizz(n, violin)
        violin[n].volume = 0.4

    tw.eat(100, 101, violin)
    tw.eat(100, 101, violin)
    tw.crop(100, violin, F(3, 8))
    violin[101].pitch = [ji.r(7, 9)]
    tw.set_pizz(101, violin)


def _adapt_viola2(viola: lily.NOventLine, vm) -> None:
    tw.crop(0, viola, F(2, 4))
    viola[1].pitch = [ji.r(48, 49)]
    tw.set_arco(1, viola)
    viola[3].pitch = [ji.r(8, 7)]
    tw.set_arco(3, viola)
    viola[3].volume = 0.6
    tw.eat(1, 2, viola)
    tw.swap_duration(2, 1, F(1, 16), viola)

    tw.crop(3, viola, F(1, 8), F(1, 16))
    viola[4].acciaccatura = None
    viola[5].acciaccatura = None
    viola[4].pitch = [ji.r(4, 3)]
    viola[5].pitch = [ji.r(7, 8)]

    viola[6].pitch = [ji.r(35, 48)]
    tw.set_pizz(6, viola)

    tw.shorten(6, F(1, 4), viola)
    tw.crop(6, viola, F(2, 4))
    viola[10].pitch = [ji.r(4, 3)]
    tw.set_arco(10, viola)

    viola[11].glissando = None
    viola[11].ornamentation = None
    tw.crop(11, viola, F(1, 8), F(1, 4))
    viola[12].pitch = [ji.r(4, 3)]

    tw.crop(14, viola, F(1, 16), F(1, 16), F(1, 8))
    viola[14].pitch = [ji.r(8, 7)]
    viola[15].pitch = [ji.r(256, 245)]
    viola[16].pitch = [ji.r(48, 49)]

    tw.crop(17, viola, F(1, 8), F(1, 8), F(1, 8))
    viola[18].pitch = [ji.r(8, 7)]
    viola[19].pitch = [ji.r(48, 49)]

    tw.rest(17, viola)
    # tw.set_arco(18, viola)
    # tw.set_arco(19, viola)
    tw.set_pizz(18, viola)
    tw.prolong(19, F(1, 8), viola)
    tw.crop(19, viola, F(1, 8))
    tw.set_pizz(19, viola)
    tw.set_arco(20, viola)

    tw.crop(21, viola, F(1, 16), F(1, 16))
    viola[22].pitch = [ji.r(4, 3)]
    # viola[23].pitch = [ji.r(4, 7)]
    tw.set_arco(22, viola)
    # tw.set_pizz(23, viola)

    tw.crop(23, viola, F(1, 8), F(1, 16), F(1, 16), F(1, 8), F(1, 16), F(1, 16))
    viola[24].pitch = [ji.r(4, 3)]
    viola[25].pitch = [ji.r(8, 7)]
    viola[26].pitch = [ji.r(48, 49)]
    viola[27].pitch = [ji.r(8, 7)]
    viola[28].pitch = [ji.r(7, 8)]

    for n in (24, 29):
        tw.set_arco(n, viola)

    tw.rest(29, viola)

    tw.crop(29, viola, F(5, 16), F(3, 16))
    viola[30].pitch = [ji.r(48, 49)]
    tw.set_arco(30, viola)

    viola[31].glissando = None
    tw.crop(31, viola, F(1, 16), F(1, 16))
    viola[31].pitch = [ji.r(8, 7)]
    tw.set_arco(31, viola)
    viola[32].pitch = [ji.r(256, 245)]

    tw.prolong(34, F(1, 8), viola)
    # viola[35].pitch = [ji.r(2, 3)]
    viola[35].ornamentation = None
    viola[36].glissando = None
    # tw.change_octave(36, -1, viola)

    tw.eat(34, 35, viola)
    tw.rest(35, viola)

    # tw.crop(34, viola, F(1, 4), F(1, 8))
    # viola[35].pitch = [ji.r(7, 8)]

    tw.shorten(34, F(3, 8), viola)

    # for n in range(31, 35):
    #     tw.set_pizz(n, viola)
    tw.set_pizz(34, viola)
    tw.postpone(34, F(1, 16), viola)

    tw.crop(36, viola, F(1, 16), F(1, 16), F(1, 4))
    viola[37].pitch = [ji.r(48, 49)]
    viola[38].pitch = [ji.r(4, 7)]

    for n in (37, 38):
        tw.set_pizz(n, viola)

    viola[40].acciaccatura = None

    viola[41].pitch = [ji.r(48, 49).register(0)]
    viola[41].volume = 0.5
    tw.set_arco(41, viola)

    tw.crop(41, viola, F(1, 16), F(1, 8))
    viola[42].pitch = [ji.r(256, 245).register(1)]

    for n in (40, 41, 42, 43):
        tw.change_octave(n, -1, viola)

    tw.crop(44, viola, F(1, 8), F(1, 16))
    viola[46].pitch = [ji.r(4, 3)]
    tw.rest(45, viola)

    tw.crop(40, viola, F(1, 8))
    tw.rest(41, viola)

    viola[50].glissando = None
    tw.set_pizz(50, viola)
    tw.set_pizz(51, viola)
    tw.set_pizz(52, viola)

    viola[52].pitch = [ji.r(8, 7)]

    viola[52].ornamentation = None
    viola[52].acciaccatura = None

    tw.eat(54, 53, viola)
    tw.eat(53, 54, viola)
    tw.set_pizz(53, viola)
    viola[53].pitch = [ji.r(48, 49)]

    tw.set_pizz(54, viola)
    viola[54].acciaccatura = None

    for n in range(56, 62):
        tw.set_pizz(n, viola)

    tw.crop(66, viola, F(1, 4), F(1, 4))
    viola[67].pitch = [ji.r(48, 49)]
    tw.set_pizz(67, viola)

    # for n in (68, 48, 47, 45, 44, 43, 42, 40):
    #     tw.set_pizz(n, viola)

    for n in (47, 42):
        tw.set_pizz(n, viola)

    for n in (68,):
        tw.set_pizz(n, viola)

    viola[48].acciaccatura = None

    viola[68].pitch = [ji.r(256, 245).register(-1)]
    viola[68].prall = None
    tw.crop(68, viola, F(1, 8))
    viola[69].pitch = [ji.r(2, 3)]

    viola[70].pitch = [ji.r(7, 8)]
    tw.set_pizz(70, viola)

    tw.change_octave(71, -1, viola)
    tw.change_octave(72, -1, viola)

    for n in range(68, 72):
        tw.set_arco(n, viola)

    # tw.set_pizz(71, viola)
    # tw.set_pizz(72, viola)
    tw.eat(71, 72, viola)
    viola[71].volume = 0.4
    viola[71].ornamentation = None
    tw.prolong(71, F(1, 8), viola)

    tw.crop(71, viola, F(1, 4))
    viola[72].pitch = [ji.r(4, 3)]

    tw.eat(72, 73, viola)
    tw.eat(72, 73, viola)

    tw.crop(72, viola, F(1, 8), position=False)
    viola[73].pitch = [ji.r(7, 4)]

    tw.crop(71, viola, F(1, 16), F(1, 16), position=False)
    tw.rest(72, viola)

    tw.postpone(68, F(1, 16), viola)

    tw.crop(67, viola, F(1, 8))
    viola[68].pitch = [ji.r(256, 245)]

    tw.crop(72, viola, F(1, 16))
    viola[73].pitch = [ji.r(2, 3)]
    tw.swap_duration(77, 78, F(1, 16), viola)

    tw.crop(78, viola, F(1, 16), F(1, 8))
    tw.set_pizz(79, viola)
    # [tw.eat(79, 80, viola) for _ in range(3)]
    tw.rest_many((80, 81, 82), viola)
    tw.postpone(79, F(1, 16), viola)

    tw.crop(77, viola, F(1, 4))
    viola[78].pitch = [ji.r(8, 5)]

    tw.set_pizz(76, viola)

    tw.rest_many((83, 85), viola)

    tw.crop(82, viola, F(1, 16), F(1, 16), F(1, 4))
    viola[83].pitch = [ji.r(4, 3)]
    tw.set_pizz(83, viola)
    viola[84].pitch = [ji.r(8, 7)]
    tw.set_pizz(84, viola)

    tw.postpone(67, F(1, 16), viola)

    tw.change_octave(30, 1, viola)

    tw.rest(86, viola)

    tw.crop(84, viola, F(3, 16))
    tw.crop(
        86,
        viola,
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(3, 16),
        F(1, 16),
        F(1, 8),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(3, 16),
        F(1, 16),
        F(1, 8),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 8),
    )

    viola[85].pitch = [ji.r(16, 7)]
    viola[86].pitch = [ji.r(2, 1)]
    viola[87].pitch = [ji.r(8, 5)]
    viola[88].pitch = [ji.r(4, 3)]
    viola[89].pitch = [ji.r(8, 7)]
    viola[90].pitch = [ji.r(2, 1)]
    viola[91].pitch = [ji.r(8, 5)]
    viola[92].pitch = [ji.r(16, 7)]
    viola[93].pitch = [ji.r(48, 49).register(0)]
    viola[94].pitch = [ji.r(8, 7).register(0)]
    viola[95].pitch = [ji.r(4, 3).register(0)]
    viola[96].pitch = [ji.r(8, 5).register(0)]
    viola[97].pitch = [ji.r(8, 7)]
    viola[98].pitch = [ji.r(1, 1)]
    viola[99].pitch = [ji.r(4, 3)]
    viola[100].pitch = [ji.r(8, 7)]
    viola[101].pitch = [ji.r(48, 49).register(-1)]
    viola[102].pitch = [ji.r(4, 3).register(0)]
    viola[103].pitch = [ji.r(8, 7).register(0)]
    for n in range(85, 104):
        tw.set_pizz(n, viola)
        viola[n].volume = 0.9
        tw.change_octave(n, -1, viola)

    # [tw.set_arco(idx + 104, viola) for idx, ev in enumerate(viola[104:])]
    # viola[106].pitch = [ji.r(48, 49).register(-1)]
    # tw.eat(101, 103, viola)
    # tw.eat(101, 102, viola)
    # viola[101].pitch = [ji.r(4, 3)]
    # tw.add_glissando(101, (0, -1), viola)

    tw.rest_many(tuple(range(104, 114)), viola)

    # tw.crop(104, viola, F(3, 8))
    # viola[104].pitch = [ji.r(4, 3).register(-1)]
    # tw.set_arco(104, viola)
    # viola[104].volume = 0.3
    # tw.postpone(104, F(1, 8), viola)

    tw.change_octave(100, 1, viola)
    tw.change_octave(101, 1, viola)

    tw.crop(104, viola, *([F(1, 8)] * 6))
    viola[104].pitch = [ji.r(4, 7)]
    viola[105].pitch = [ji.r(7, 8)]
    viola[106].pitch = [ji.r(35, 24)]
    tw.eat(106, 107, viola)
    viola[107].pitch = [ji.r(2, 3)]
    viola[108].pitch = [ji.r(4, 7)]

    for n in range(104, 109):
        tw.set_pizz(n, viola)
        viola[n].volume = 0.7

    viola[109].pitch = [ji.r(7, 8)]
    tw.set_pizz(109, viola)
    tw.crop(109, viola, F(1, 8))
    viola[110].pitch = [ji.r(35, 24)]
    # tw.change_octave(110, -1, viola)


def _adapt_cello2(cello: lily.NOventLine, vm) -> None:
    cello[1].pitch = [ji.r(72, 49).register(-1)]
    cello[1].optional = None
    cello[1].choose = None
    cello[2].pitch = [ji.r(384, 245).register(-1)]
    tw.set_arco(2, cello)

    cello[5].pitch = [ji.r(7, 24)]
    tw.shorten(5, F(1, 4), cello)
    tw.set_pizz(5, cello)
    tw.crop(5, cello, F(2, 4))

    cello[8].pitch = [ji.r(1, 1)]
    tw.eat(8, 9, cello)
    cello[9].pitch = [ji.r(16, 15)]
    cello[9].prall = None
    tw.set_arco(9, cello)
    cello[10].pitch = [ji.r(1, 1)]
    tw.set_arco(10, cello)

    tw.prolong(10, F(1, 4), cello)
    tw.crop(10, cello, F(1, 4))
    # tw.change_octave(11, -1, cello)
    tw.add_glissando(8, (0, 0, 1), cello, durations=[F(3, 16), F(1, 16)])

    cello[11].volume = 0.38
    tw.crop(11, cello, F(1, 8), F(1, 16), F(1, 16))
    cello[11].natural_harmonic = attachments.NaturalHarmonic()
    cello[12].pitch = [ji.r(6, 7)]
    cello[13].pitch = [ji.r(384, 245).register(-1)]
    cello[14].pitch = [ji.r(72, 49).register(-1)]
    cello[15].pitch = [ji.r(12, 7).register(-1)]
    cello[16].pitch = [ji.r(384, 245).register(-1)]

    cello[14].volume = 0.38
    cello[15].volume = 0.38
    cello[16].volume = 0.38

    tw.prolong(16, F(1, 32), cello)
    # tw.shorten(15, F(1, 16), cello)
    tw.swap_duration(15, 16, F(1, 16), cello)
    tw.set_pizz(15, cello)
    tw.crop(16, cello, F(1, 8))
    tw.set_pizz(16, cello)
    tw.set_arco(17, cello)
    # tw.shorten(17, F(1, 16), cello)

    cello[19].pitch = [ji.r(256, 189).register(-1)]
    cello[19].volume = 0.24
    tw.rest(20, cello)

    tw.shorten(19, F(1, 16), cello)

    tw.crop(20, cello, F(1, 16), F(1, 16), F(1, 8), F(1, 16), F(1, 16))
    cello[21].pitch = [ji.r(12, 7).register(-1)]
    tw.set_arco(21, cello)

    cello[22].pitch = [ji.r(72, 49).register(-1)]
    tw.set_arco(22, cello)
    cello[22].volume = 0.65

    cello[23].pitch = [ji.r(12, 7).register(-1)]
    tw.set_arco(23, cello)

    cello[24].pitch = [ji.r(7, 6).register(0)]
    tw.set_arco(24, cello)

    tw.rest(25, cello)
    tw.crop(25, cello, F(1, 16), F(3, 16), F(1, 16), F(3, 16))
    cello[26].pitch = [ji.r(1, 1).register(0)]
    tw.set_arco(26, cello)
    cello[26].volume = 0.8

    cello[28].pitch = [ji.r(72, 49).register(-1)]
    tw.set_arco(28, cello)
    cello[28].volume = 0.5

    cello[29].optional = None
    # cello[30].pitch = [ji.r(72, 49).register(-1)]
    tw.set_arco(29, cello)
    cello[29].volume = 0.5
    cello[29].acciaccatura = None

    tw.prolong(29, F(1, 16), cello)
    tw.crop(29, cello, F(1, 16), F(1, 16))
    cello[29].pitch = [ji.r(12, 7).register(-1)]
    cello[30].pitch = [ji.r(72, 49).register(-1)]

    # cello[33].ornamentation = None
    # cello[33].volume = 0.5
    # tw.crop(33, cello, F(1, 8), F(3, 16), F(1, 16), F(1, 16), F(3, 16))
    # cello[35].pitch = [ji.r(8, 15)]
    # cello[36].pitch = [ji.r(1, 2)]
    # cello[37].pitch = [ji.r(3, 7)]

    # tw.crop(18, cello, F(1, 16), F(1, 16))
    # cello[19].pitch = [ji.r(16, 15).register(-1)]
    # tw.set_arco(19, cello)

    tw.crop(4, cello, F(1, 8), F(1, 16), F(1, 16))
    cello[5].acciaccatura = None
    cello[6].acciaccatura = None

    tw.rest(35, cello)
    tw.crop(34, cello, F(1, 8))
    cello[34].pitch = [ji.r(6, 7)]

    tw.set_pizz(34, cello)
    tw.postpone(34, F(1, 16), cello)

    tw.crop(36, cello, F(1, 16), F(1, 16), F(1, 4))
    cello[37].pitch = [ji.r(384, 245).register(-1)]
    cello[38].pitch = [ji.r(3, 7)]

    for n in (37, 38):
        tw.set_pizz(n, cello)

    tw.rest(40, cello)

    tw.crop(39, cello, F(1, 4))
    cello[40].pitch = [ji.r(7, 24)]
    tw.set_arco(40, cello)

    cello[42].acciaccatura = None
    cello[42].ornamentation = None
    cello[42].pitch = [ji.r(72, 49)]
    tw.add_artifical_harmonic(42, ji.r(72, 49).register(-2), cello)
    tw.swap_duration(42, 41, F(1, 8), cello)

    tw.change_octave(40, 1, cello)

    for n in (41, 42):
        tw.change_octave(n, -2, cello)
        cello[n].artifical_harmonic = None
        tw.set_arco(n, cello)

    tw.crop(42, cello, F(1, 8))
    tw.copy_pitch(41, 43, cello)

    # tw.postpone(44, F(1, 8), cello)
    tw.set_arco(44, cello)
    tw.change_octave(44, -1, cello)
    tw.shorten(44, F(1, 8), cello)

    tw.swap_duration(43, 44, F(1, 16), cello)
    tw.crop(43, cello, F(1, 8))
    tw.rest(44, cello)

    tw.crop(40, cello, F(1, 8))
    tw.rest(41, cello)

    tw.crop(46, cello, F(1, 16))
    cello[46].pitch = [ji.r(7, 24)]

    tw.rest_many((49, 51), cello)

    tw.crop(48, cello, F(1, 8) + F(1, 4), F(1, 4), F(1, 4))
    cello[49].pitch = [ji.r(7, 6).register(-2)]
    cello[50].pitch = [ji.r(72, 49).register(-2)]
    tw.set_pizz(49, cello)
    tw.set_pizz(50, cello)

    tw.rest(52, cello)
    tw.rest(52, cello)
    # tw.shorten(52, F(1, 16), cello)

    tw.crop(53, cello, F(1, 4), F(1, 8), F(1, 8))
    cello[54].pitch = [ji.r(72, 49).register(-2)]
    cello[55].pitch = [ji.r(384, 245).register(-2)]
    cello[57].pitch = [ji.r(1, 2)]
    cello[57].optional = None

    cello[58].pitch = [ji.r(7, 12)]

    tw.swap_duration(56, 57, F(1, 16), cello)
    tw.swap_duration(57, 58, F(1, 4), cello)

    # for n in (54, 55, 56, 57, 58, 47, 46, 44, 43, 42, 40):
    #     tw.set_pizz(n, cello)

    for n in (46, 42):
        tw.set_pizz(n, cello)

    for n in (54, 55, 56, 57, 58):
        tw.set_pizz(n, cello)

    tw.crop(58, cello, F(1, 8))
    cello[59].pitch = [ji.r(8, 15)]
    tw.set_arco(59, cello)
    cello[59].volume = 0.3

    for n in range(57, 59):
        tw.set_arco(n, cello)

    tw.swap_duration(57, 56, F(1, 16), cello)
    tw.add_glissando(58, (0, 0, -1), cello, durations=[F(2, 16), F(1, 16)])
    tw.swap_duration(59, 58, F(1, 16), cello)

    tw.copy_pitch(54, 56, cello)

    tw.crop(59, cello, F(3, 16))
    tw.copy_pitch(58, 60, cello)
    # cello[60].pitch = [ji.r(7, 24)]

    cello[61].pitch = [ji.r(1, 2)]
    cello[61].optional = None
    cello[61].prall = None
    tw.set_arco(61, cello)

    tw.set_arco(56, cello)
    # for n in (57, 58, 59, 60, 61):
    #     tw.change_octave(n, -1, cello)
    #     cello[n].volume = 0.6

    tw.crop(61, cello, F(1, 8))
    tw.copy_pitch(60, 62, cello)
    tw.eat(62, 63, cello)

    # tw.shorten(59, F(1, 16), cello)
    tw.crop(59, cello, F(1, 16), F(1, 16), position=False)
    tw.rest(60, cello)
    # tw.crop(62, cello, F(1, 16))
    tw.swap_duration(62, 63, F(1, 16), cello)
    # cello[63].pitch = [ji.r(1, 2)]
    # tw.change_octave(64, -1, cello)
    tw.set_pizz(61, cello)

    tw.crop(64, cello, F(1, 8))
    tw.set_pizz(65, cello)
    tw.change_octave(65, -1, cello)
    # tw.eat(65, 66, cello)
    # tw.eat(65, 66, cello)
    tw.rest_many((66, 67), cello)

    tw.postpone(65, F(1, 16), cello)

    tw.rest_many((67, 68, 69, 70, 71, 72, 73, 74, 75, 76), cello)

    tw.crop(67, cello, F(1, 16), F(1, 4))
    cello[68].pitch = [ji.r(256, 189).register(-1)]
    tw.set_pizz(68, cello)

    tw.postpone(54, F(1, 16), cello)

    # tw.change_octave(28, 1, cello)
    cello[28].natural_harmonic = attachments.NaturalHarmonic()
    tw.change_octave(30, 1, cello)
    tw.add_artifical_harmonic(30, cello[30].pitch[0] - ji.r(4, 1), cello)

    tw.crop(68, cello, F(3, 16))
    tw.crop(70, cello, F(1, 8), F(1, 8))

    tw.eat(69, 70, cello)
    cello[69].pitch = [ji.r(12, 7)]
    cello[70].pitch = [ji.r(2, 1)]
    tw.set_arco(69, cello)
    tw.set_arco(70, cello)

    # tw.crop(71, cello, *([F(1, 8)] * 12))
    pcycle = infit.Cycle((ji.r(256, 189), ji.r(12, 7), ji.r(2, 1)))
    rcycle = infit.Cycle((F(1, 16), F(3, 16), F(1, 8)))
    for n in range(12):
        idx = n + 71
        tw.crop(idx, cello, next(rcycle))
        cello[idx].pitch = [next(pcycle)]
        tw.set_arco(idx, cello)

    tw.crop(73, cello, F(1, 16))
    cello[73].pitch = [ji.r(32, 15)]

    tw.crop(82, cello, F(1, 8))
    cello[83].pitch = [ji.r(32, 15)]
    tw.crop(84, cello, F(1, 16))
    cello[85].pitch = [ji.r(32, 15)]

    [tw.set_arco(idx + 86, cello) for idx, ev in enumerate(cello[86:])]
    for idx in range(69, 86):
        tw.change_octave(idx, -2, cello)
        tw.set_pizz(idx, cello)
        # cello[idx].volume = 0.8
        cello[idx].volume = 0.9

    tw.rest_many(tuple(range(86, 94)), cello)

    # tw.crop(86, cello, F(3, 8))
    # cello[86].pitch = [ji.r(1, 1)]
    # tw.set_arco(86, cello)
    # cello[86].volume = 0.3
    # tw.postpone(86, F(1, 8), cello)
    tw.crop(86, cello, F(1, 16), F(1, 16), F(3, 16), F(1, 16), F(1, 8), F(1, 4))
    cello[86].pitch = [ji.r(3, 7)]
    cello[87].pitch = [ji.r(256, 189).register(-2)]
    cello[89].pitch = [ji.r(7, 12)]
    cello[90].pitch = [ji.r(7, 24)]
    cello[91].pitch = [ji.r(1, 2)]

    for n in range(86, 92):
        if cello[n].pitch:
            tw.set_pizz(n, cello)
            cello[n].volume = 0.7

    cello[92].pitch = [ji.r(7, 12)]
    tw.set_pizz(92, cello)

    tw.crop(92, cello, F(1, 8), F(3, 16), F(1, 16))
    tw.change_octave(93, -1, cello)

    cello[94].pitch = [ji.r(1, 2)]
    cello[95].pitch = [ji.r(1, 1)]

    cello[94].natural_harmonic = attachments.NaturalHarmonic()
    cello[95].natural_harmonic = attachments.NaturalHarmonic()


def _adapt_left2(left: lily.NOventLine, vm) -> None:
    tw.add_gong(3, left, ji.r(72, 49))
    left[3].pitch.extend([ji.r(48, 49).register(-2)])
    left[4].optional = False
    left[6].pitch = [ji.r(35, 24)]
    left[6].volume = 0.8
    tw.crop(6, left, F(1, 8), F(1, 16))
    left[6].pitch = [ji.r(35, 32)]
    left[8].pitch = [ji.r(7, 8)]
    # tw.add_acciaccatura(6, ji.r(35, 32), left)

    tw.crop(0, left, F(3, 16), F(1, 16), F(1, 16), F(1, 16))
    left[0].pitch = [ji.r(48, 49).register(-3), ji.r(72, 49).register(-2)]
    left[1].pitch = [ji.r(288, 245).register(-1), ji.r(384, 245).register(-2)]
    left[2].pitch = [ji.r(48, 49).register(-2), ji.r(72, 49).register(-2)]
    left[3].pitch = [ji.r(256, 245).register(-1)]
    left[4].pitch = [ji.r(288, 245).register(-1)]

    tw.crop(5, left, F(1, 16))

    tw.crop(6, left, F(1, 16))
    left[5].pitch = [ji.r(256, 245).register(0)]
    left[6].pitch = [ji.r(288, 245).register(0)]
    left[7].pitch = [ji.r(72, 49).register(0)]

    tw.crop(15, left, F(1, 4), F(3, 16), F(5, 16), F(3, 16), F(1, 16))
    tw.add_kenong(15, left, ji.r(35, 24))
    left[15].volume = 1
    for n in range(16, 20):
        if n in (16, 18):
            left[n].pitch = [ji.r(7, 8)]
            left[n].volume = 0.8
        else:
            left[n].pitch = [ji.r(7, 9)]
            left[n].volume = 0.5

        left[n].ottava = attachments.Ottava(0)

    # left[18].pitch.append(ji.r(7, 6))

    left[21].pitch.append(ji.r(3, 4))
    left[21].optional_some_pitches = None
    tw.eat(22, 23, left)
    tw.crop(22, left, F(1, 4))
    left[22].pitch.append(ji.r(1, 1))
    left[23].pitch.append(ji.r(8, 15))

    left[21].arpeggio = attachments.Arpeggio(abjad.enums.Down)

    left[24].volume = 0.8
    tw.crop(24, left, F(1, 16), F(1, 16), F(1, 16), F(1, 16), F(1, 16))

    left[25].pitch = [ji.r(4, 5)]
    left[26].pitch = [ji.r(1, 1)]
    left[27].pitch = [ji.r(7, 9)]
    left[28].pitch = [ji.r(4, 3)]

    left[30].pitch = [ji.r(4, 7)]
    left[31].pitch = [
        ji.r(288, 245).register(keyboard.SYMBOLIC_GONG_OCTAVE),
        ji.r(48, 49).register(-2),
        ji.r(72, 49).register(-2),
        # ji.r(288, 245),
    ]

    tw.rest_many((32, 33, 34), left)
    tw.prolong(31, F(1, 16), left)
    tw.crop(32, left, F(1, 8), F(3, 16))
    tw.add_kenong(32, left, ji.r(288, 245))
    tw.add_kenong(33, left, ji.r(384, 245))
    tw.add_gong(34, left, ji.r(8, 7))
    # tw.add_kenong(35, left, ji.r(64, 63))
    tw.rest_many((35, 36), left)

    left[32].volume = 0.7
    left[33].volume = 1

    left[35].ottava = attachments.Ottava(0)
    left[35].pedal = attachments.Pedal(False)

    tw.add_kenong(36, left, ji.r(3, 2))
    tw.eat(36, 37, left)
    tw.eat(36, 37, left)

    tw.crop(36, left, F(1, 4))
    tw.add_kenong(37, left, ji.r(72, 49))

    tw.crop(36, left, F(1, 8), F(1, 8))
    tw.crop(38, left, F(1, 8), F(1, 8))

    left[37].pitch = [ji.r(1, 1).register(-2)]
    left[39].pitch = [ji.r(48, 49).register(-3)]

    left[36].volume = 1.2
    left[38].volume = 1.2

    tw.make_solo_gong(40, left)

    tw.rest_many((41, 42, 43), left)

    tw.eat(40, 41, left)

    tw.swap_duration(40, 41, F(3, 16), left)
    tw.eat(41, 42, left)
    left[41].volume = 0.43
    left[41].articulation_once = None
    tw.crop(
        41,
        left,
        F(3, 32),
        F(1, 32),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(3, 32),
        F(1, 32),
        F(2, 32),
    )
    # left[41].pitch = [ji.r(3, 8)]
    left[41].pitch = []
    # left[42].pitch = [ji.r(4, 7)]
    left[42].pitch = [ji.r(3, 8), ji.r(4, 7)]
    # left[42].arpeggio = attachments.Arpeggio(abjad.enums.Up)
    left[43].pitch = [ji.r(1, 1)]
    left[44].pitch = [ji.r(7, 8)]
    left[45].pitch = [ji.r(7, 6)]
    left[46].pitch = [ji.r(35, 32)]
    left[47].pitch = [ji.r(35, 24)]
    left[48].pitch = [ji.r(4, 3)]
    left[49].pitch = [ji.r(7, 6), ji.r(7, 8)]
    left[49].volume = 0.37

    tw.crop(39, left, F(1, 16))
    left[39].pitch = [ji.r(72, 49).register(-2)]

    tw.crop(37, left, F(1, 16))
    left[38].pitch = [ji.r(3, 8)]

    tw.crop(18, left, F(1, 16))
    left[18].pitch = [ji.r(7, 6)]

    tw.crop(52, left, F(1, 8), F(1, 16))
    left[53].pitch = [ji.r(1, 1), ji.r(3, 4)]

    left[54].volume = 0.37
    left[54].pitch = [ji.r(288, 245).register(0)]

    tw.crop(54, left, F(1, 16), F(1, 16), F(1, 16))
    left[55].pitch = [ji.r(384, 245).register(0)]
    left[56].pitch = [ji.r(256, 245).register(0)]
    left[57].pitch = [ji.r(72, 49).register(0)]

    left[58].articulation_once = None
    left[58].arpeggio = None
    left[58].pitch = [ji.r(384, 245).register(0)]
    left[58].volume = 0.36

    tw.crop(58, left, F(1, 16), F(1, 16), F(1, 16))
    left[59].pitch = [ji.r(12, 7)]
    left[60].pitch = [ji.r(4, 3).register(0)]

    left[61].volume = 0.36
    tw.crop(61, left, F(1, 16), F(2, 16), F(1, 16), F(1, 16))
    left[61].pitch = [ji.r(7, 6)]
    left[62].pitch = [ji.r(4, 5), ji.r(1, 1)]
    left[63].pitch = [ji.r(7, 8)]
    left[64].pitch = [ji.r(7, 9)]

    tw.eat(66, 65, left)
    left[65].optional = None
    left[65].volume = 0.34
    left[68].volume = 0.34

    tw.crop(65, left, F(1, 16), F(1, 16), F(1, 16))
    left[65].pitch = [ji.r(4, 5)]
    left[66].pitch = [ji.r(1, 1)]
    left[67].pitch = [ji.r(7, 8)]
    left[68].pitch = [ji.r(7, 9)]

    tw.crop(68, left, F(2, 16), F(1, 16), F(1, 16), F(1, 32), F(1, 32))
    left[69].pitch = [ji.r(7, 6)]
    left[70].pitch = [ji.r(7, 8)]
    left[72].pitch = [ji.r(4, 7)]

    left[73].arpeggio = None
    left[73].articulation_once = None
    left[73].pitch = [ji.r(288, 245).register(-1)]
    left[74].pitch = [ji.r(48, 49).register(-2)]

    left[74].volume = 0.34
    tw.crop(74, left, F(2, 32))
    # left[75].pitch = [ji.r(48, 49).register(-3)]
    left[75].pitch = [ji.r(4, 7)]

    tw.add_gong(76, left, ji.r(64, 63))
    left[76].arpeggio = None
    left[76].articulation_once = None

    tw.rest_many((77, 78), left)

    tw.make_solo_gong(79, left)

    tw.crop(73, left, F(1, 16), F(1, 16))
    left[74].pitch = [ji.r(48, 49).register(-2)]
    left[75].pitch = [ji.r(64, 63).register(-1)]
    tw.eat(71, 72, left)

    tw.rest(78, left)
    tw.eat(76, 77, left)
    # tw.eat(77, 78, left)
    tw.rest(78, left)
    tw.prolong(77, F(1, 16) + F(1, 4), left)

    tw.eat(52, 53, left)

    tw.rest_many((81, 82, 83), left)

    tw.add_gong(81, left, ji.r(72, 49))
    tw.add_gong(82, left, ji.r(1, 1))

    tw.swap_duration(72, 71, F(1, 32), left)

    tw.rest(84, left)

    tw.crop(83, left, F(1, 16), F(1, 16), F(1, 8), F(1, 4))
    tw.add_kenong(84, left, ji.r(1, 1))
    tw.add_kenong(85, left, ji.r(14, 9))
    tw.add_kenong(86, left, ji.r(64, 63))

    tw.rest_many((88, 89, 90, 91, 92, 93, 94, 95), left)

    """
    tw.crop(87, left, F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4), F(1, 4))
    tw.add_gong(87, left, ji.r(8, 7))
    tw.add_kenong(88, left, ji.r(64, 63))
    tw.add_gong(89, left, ji.r(8, 5))
    tw.add_kenong(90, left, ji.r(3, 2))
    tw.add_gong(91, left, ji.r(64, 63))
    tw.add_kenong(92, left, ji.r(1, 1))
    tw.add_kenong(93, left, ji.r(8, 7))

    for n in (90, 93):
        left[n].volume = 1.2
    """
    # tw.crop(87, left, *([F(1, 32)] + ([F(1, 16)] * 27) + [F(1, 32)]))
    cropcycle = infit.Cycle(
        (F(3, 32), F(1, 32), F(2, 32), F(2, 32), F(2, 32), F(2, 32), F(3, 32), F(1, 32))
    )
    # tw.crop(87, left, *([F(1, 16)] * 28))
    tw.crop(87, left, *[next(cropcycle) for _ in range(28)])
    tw.add_gong(87, left, ji.r(8, 7))
    tw.add_kenong(91, left, ji.r(64, 63))
    tw.add_gong(95, left, ji.r(8, 5))
    tw.add_kenong(99, left, ji.r(3, 2))
    tw.add_gong(103, left, ji.r(64, 63))
    tw.add_kenong(107, left, ji.r(1, 1))
    tw.add_kenong(111, left, ji.r(8, 7))

    for idx, p in enumerate(
        (
            (1, 1),
            (4, 5),
            (1, 1),
            (7, 9),
            (256, 189 * 2),
            (64, 63),
            (3, 4),
            (1, 1),
            (4, 5),
            (3, 4),
            (64, 63),
            (3, 4),
            (4, 7),
            (3, 4),
            (1, 1),
            (7, 9),
            (256, 189 * 2),
            (64, 63),
            (3, 4),
            (4, 7),
            (1, 1),
            (3, 4),
            (64, 63),
            (3, 4),
            (4, 7),
            (4, 5),
            (1, 1),
            (4, 5),
        )
    ):
        locidx = idx + 87
        pitch = ji.r(*p)

        if left[locidx].pitch:
            left[locidx].pitch.append(pitch)
        else:
            left[locidx].pitch = [pitch]

        left[locidx].volume = 0.5
        left[locidx].ottava = attachments.Ottava(0)

    # tw.add_gong(87, left, ji.r(8, 7))
    tw.rest(115, left)
    tw.crop(
        115,
        left,
        F(3, 16),
        F(1, 16),
        F(1, 8),
        F(1, 8),
        F(1, 16),
        F(1, 16),
        F(1, 16),
        F(1, 16),
    )
    tw.add_gong(115, left, ji.r(8, 7))
    left[115].pitch.append(ji.r(256, 189).register(-1))
    left[116].pitch = [ji.r(3, 2).register(-1)]
    left[117].pitch = [ji.r(7, 4).register(-1), ji.r(35, 32)]
    left[118].pitch = [ji.r(1, 1).register(0)]
    left[119].pitch = [ji.r(14, 9).register(-1)]
    left[120].pitch = [ji.r(1, 1).register(0)]
    left[121].pitch = [ji.r(4, 3).register(0)]
    left[122].pitch = [ji.r(7, 6).register(0)]

    tw.crop(123, left, F(1, 8), F(3, 16), F(1, 16))
    tw.add_kenong(123, left, ji.r(35, 24))
    tw.add_gong(124, left, ji.r(7, 6))
    # tw.add_kenong(125, left, ji.r(7, 6))
    left[125].pitch = [ji.r(7, 24)]
    left[125].ottava = attachments.Ottava(-1)
    tw.add_kenong(126, left, ji.r(14, 9))

    tw.swap_duration(115, 116, F(1, 8), left)
    tw.crop(116, left, F(1, 16), F(1, 16))
    left[116].pitch = [ji.r(64, 63).register(-1)]
    left[117].pitch = [ji.r(7, 4).register(-1)]


def _adapt_right2(right: lily.NOventLine, vm) -> None:
    tw.swap_duration(0, 1, F(3, 16), right)
    right[1].optional_some_pitches = None
    right[2].optional_some_pitches = None
    right[2].pitches = [ji.r(144, 49), ji.r(288, 245).register(1)]
    right[3].optional_some_pitches = None

    right[4].pitch = [ji.r(35, 24).register(1), ji.r(35, 32).register(1)]
    tw.postpone(4, F(3, 8), right)
    tw.crop(5, right, F(1, 8), F(3, 8), F(1, 8))
    tw.rest(6, right)
    # tw.rest(8, right)

    tw.crop(9, right, F(1, 4))
    right[9].pitch.append(ji.r(2, 1))
    right[10].pitch.append(ji.r(16, 15))
    # right[9].pitch.append(ji.r(16, 3))

    tw.shorten(10, F(1, 8), right)
    tw.crop(11, right, F(1, 8), F(1, 8), F(1, 16))
    right[11].pitch = [ji.r(2, 1), ji.r(8, 5)]
    right[12].pitch = [ji.r(7, 9), ji.r(2, 3)]
    tw.rest(13, right)

    right[15].pitch = [ji.r(48, 49).register(-1), ji.r(72, 49).register(-1)]

    tw.crop(15, right, F(1, 4), F(1, 8), F(1, 4))
    tw.rest(16, right)

    tw.postpone(18, F(1, 8), right)
    tw.rest(21, right)

    tw.crop(20, right, F(3, 8), F(1, 4), F(1, 4))
    right[21].pitch = [ji.r(2, 1), ji.r(3, 2)]
    right[22].pitch = [ji.r(48, 49).register(-1), ji.r(72, 49).register(-1)]

    tw.crop(20, right, F(1, 8), F(1, 8))
    right[21].pitch = [ji.r(48, 49).register(-1), ji.r(72, 49).register(-1)]

    right[19].pitch.append(ji.r(256, 189))

    tw.rest(26, right)

    right[25].optional_some_pitches = None
    tw.postpone(25, F(1, 8), right)

    tw.eat(29, 28, right)
    right[28].pitch = [ji.r(35, 24), ji.r(7, 4)]
    right[29].pitch = [ji.r(384, 245).register(1), ji.r(288, 245).register(1)]

    tw.prolong(29, F(1, 32), right)

    tw.postpone(28, F(1, 8), right)

    tw.rest_many((33, 34, 35, 37, 38), right)
    tw.shorten(34, F(1, 8), right)

    right[36].optional_some_pitches = None

    tw.postpone(29, F(1, 16), right)
    tw.shorten(28, F(3, 16), right)

    tw.crop(43, right, F(1, 4))
    right[44].pitch = [ji.r(14, 9)]
    right[45].pitch = [ji.r(2, 1)]

    tw.eat(45, 46, right)

    tw.rest(48, right)
    tw.rest(46, right)

    tw.swap_duration(34, 35, F(1, 16), right)
    tw.shorten(35, F(1, 8), right)

    tw.rest_many((47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58), right)


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        5,
        # tempo_factor=0.35,
        tempo_factor=0.31,
        # tempo_factor=0.26,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.7,
        # ro_temperature=0.61,
        ro_temperature=0.585,
        # ro_density=0.684,
        ro_density=0.68,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.35, 0.05),
        area_density_reference_size=F(1, 2),
        area_min_split_size=F(4, 16),
    )

    vm.remove_area(0, 2)
    vm.remove_area(16, 19)
    vm.remove_area(33, 34)
    # vm.repeat_area(3, 11)  # first loop ... perhaps too much
    vm.add_bar(10, abjad.TimeSignature((1, 4)))

    # commented for remove area later
    vm.repeat_area(18, 21)

    # uncommented
    # vm.repeat_area(38, 42)

    vm.add_bar(11, abjad.TimeSignature((1, 4)))
    vm.add_bar(21, abjad.TimeSignature((2, 4)))
    # vm.add_bar(37, abjad.TimeSignature((2, 4)))
    # vm.add_bar(14, abjad.TimeSignature((1, 4)))

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            tremolo_maker=infit.ActivityLevel(0),
            acciaccatura_maker=infit.ActivityLevel(4),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(8),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 0, 1)),
            harmonic_pitches_activity=0.8,
            harmonic_pitches_density=0.87,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(3, 32),
            optional_pitches_avg_size=F(3, 16),
            optional_pitches_density=0.8,
            after_glissando_size=F(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(3, start_at=2),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(9),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2, 0, 1)),
            harmonic_pitches_activity=0.8,
            harmonic_pitches_density=0.94,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=F(1, 8),
            optional_pitches_avg_size=F(1, 4),
            optional_pitches_density=0.7,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(3),
            acciaccatura_maker=infit.ActivityLevel(3),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(9),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 1)),
            shall_add_optional_pitches=True,
            harmonic_pitches_activity=0.8,
            harmonic_pitches_density=0.87,
            optional_pitches_min_size=F(1, 8),
            optional_pitches_avg_size=F(3, 16),
            optional_pitches_density=0.7,
        ),
        keyboard=keyboard.KeyboardMaker(
            lh_min_metricity_to_add_harmony=0.4,
            lh_min_metricity_to_add_accent=1.5,
            lh_max_metricity_for_arpeggio=0.95,
            lh_min_metricity_to_add_restricted_harmony=0,
            lh_prohibit_repetitions=True,
            lh_add_repetitions_avoiding_notes=True,
            rh_likelihood_making_harmony=0.95,
            harmonies_max_difference=1200,
            harmonies_min_difference=250,
            colotomic_structure=(1, 2, 0, 2),
        ),
    )

    _adapt_violin(vm.violin.musdat[1], vm)
    _adapt_viola(vm.viola.musdat[1], vm)
    _adapt_cello(vm.cello.musdat[1], vm)
    _adapt_keyboard(vm.keyboard.musdat[2], vm.keyboard.musdat[1], vm)

    vm.add_bar(2, abjad.TimeSignature((4, 4)))

    vm.force_remove_area(len(vm.violin.bars) - 31, len(vm.violin.bars) - 28)
    vm.force_remove_area(28, 29)
    vm.force_remove_area(21, 26)

    # second round of postprocessing
    _adapt_violin2(vm.violin.musdat[1], vm)
    _adapt_viola2(vm.viola.musdat[1], vm)
    _adapt_cello2(vm.cello.musdat[1], vm)
    _adapt_left2(vm.keyboard.musdat[2], vm)
    _adapt_right2(vm.keyboard.musdat[1], vm)

    vm.force_remove_area(len(vm.violin.bars) - 10, len(vm.violin.bars))

    """
    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            nth_line = (2, 1)
        else:
            nth_line = (1,)

        novent_line = getattr(vm, instr).musdat[nth_line[0]]
        novent_line[0].dynamic = attachments.Dynamic("p")
    """

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

    verse = vm()

    # rit_start_text_span = abjad.StartTextSpan(
    #     left_text=abjad.Markup(
    #         r'\italic {"rit."} \hspace #0.5 \teeny {"(when repeating)"}'
    #     ),
    #     direction=abjad.Up,
    # )
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

            """
            if instr == "keyboard":
                if idx[1] == 0:
                    abjad.attach(rit_start_text_span, staff[-4][0])
                    abjad.attach(abjad.StopTextSpan(), staff[-1][-1])
            else:
                abjad.attach(rit_start_text_span, staff[-4][0])
                abjad.attach(abjad.StopTextSpan(), staff[-1][-1])
            """

            # adapting accidental notation of keyboard
            if instr == "keyboard" and idx[1] == 0:
                abjad.Accidental.respell_with_sharps(staff[0])
                abjad.Accidental.respell_with_sharps(staff[1])
                abjad.Accidental.respell_with_sharps(staff[2])
                abjad.Accidental.respell_with_sharps(staff[3])

                for n in (18, 19, 20):
                    staff[n] = abjad.mutate(getattr(verse, instr).abjad[1][1][n]).copy()
                    for idx, tone in enumerate(staff[n]):
                        if idx % 4 == 0:
                            staff[n][idx] = abjad.Note(
                                staff[n][idx].written_pitches[1],
                                staff[n][idx].written_duration,
                            )
                            abjad.attach(abjad.StartBeam(), staff[n][idx])
                            # abjad.attach(abjad.StopBeam(), staff[n][idx + 3])

                abjad.detach(abjad.TimeSignature, staff[18][0])
                abjad.attach(abjad.Clef("bass"), staff[18][0])
                # abjad.attach(abjad.Clef("bass"), staff[18][0])
                staff[21] = abjad.mutate(getattr(verse, instr).abjad[1][1][21]).copy()
                staff[21][0] = abjad.Note(
                    staff[21][0].written_pitches[1], staff[21][0].written_duration,
                )
                abjad.attach(abjad.StartBeam(), staff[21][0])
                abjad.attach(abjad.Dynamic("ppp"), staff[18][0])

            elif instr == "keyboard" and idx[1] == 1:
                abjad.Accidental.respell_with_sharps(staff[0])
                abjad.Accidental.respell_with_sharps(staff[1])
                abjad.Accidental.respell_with_sharps(staff[3])

                for n in (18, 19, 20):
                    new_bar = abjad.Container([])
                    for idx, tone in enumerate(staff[n]):
                        if idx % 4 == 0:
                            new_bar.append(
                                abjad.Note(staff[n][idx].written_pitches[0], F(1, 4))
                            )

                    staff[n] = new_bar

                staff[21] = abjad.Container(
                    [abjad.Note(staff[21][0].written_pitches[0], F(3, 4))]
                )
                abjad.attach(abjad.Ottava(-1), staff[21][0])
                abjad.attach(abjad.StartPianoPedal("sustain"), staff[21][0])

                abjad.attach(abjad.Dynamic("pp"), staff[0][0])
                abjad.attach(abjad.StartHairpin(), staff[0][0])
                abjad.attach(abjad.Dynamic("p"), staff[1][0])
                abjad.attach(abjad.StartHairpin(">"), staff[1][4])
                abjad.attach(abjad.Dynamic("pp"), staff[2][0])
                abjad.attach(abjad.StartHairpin(), staff[2][4])
                abjad.attach(abjad.Dynamic("p"), staff[3][0])

                abjad.attach(abjad.Dynamic("ppp"), staff[8][-3])
                abjad.attach(abjad.StartHairpin(">"), staff[11][8])
                abjad.attach(abjad.Dynamic("pppp"), staff[11][-1])
                abjad.attach(abjad.Dynamic("pp"), staff[12][0])
                abjad.attach(abjad.Dynamic("p"), staff[14][0])

                abjad.attach(
                    abjad.Articulation("accent", direction=abjad.enums.Up), staff[1][4]
                )

            elif instr == "violin":
                abjad.attach(abjad.Dynamic("ppp"), staff[0][2])
                abjad.attach(abjad.StartHairpin(), staff[0][2])
                abjad.attach(abjad.Dynamic("p"), staff[1][3])
                abjad.attach(abjad.StartHairpin(">"), staff[1][3])
                abjad.attach(abjad.Dynamic("pp"), staff[2][0])
                abjad.attach(abjad.Dynamic("p"), staff[3][2])
                abjad.attach(abjad.Dynamic("ppp"), staff[5][-1])

                abjad.attach(abjad.Dynamic("p"), staff[7][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[8][0])
                abjad.attach(abjad.Dynamic("p"), staff[8][3])

                abjad.attach(abjad.Dynamic("pp"), staff[9][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[12][0])
                abjad.attach(abjad.Dynamic("p"), staff[14][0])

                abjad.attach(abjad.Articulation("tenuto"), staff[1][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[1][4])

                abjad.attach(abjad.Articulation("tenuto"), staff[5][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[5][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[6][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[6][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[9][1])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][3])

                abjad.attach(abjad.Dynamic("ppp"), staff[17][-1])

                abjad.attach(
                    abjad.Articulation("accent", direction=abjad.enums.Up), staff[20][8]
                )
                abjad.attach(
                    abjad.Articulation("accent", direction=abjad.enums.Up),
                    staff[20][10],
                )

            elif instr == "viola":
                abjad.attach(abjad.Dynamic("ppp"), staff[0][1])
                abjad.attach(abjad.StartHairpin(), staff[0][1])
                abjad.attach(abjad.Dynamic("p"), staff[1][2])
                abjad.attach(abjad.StartHairpin(">"), staff[1][2])
                abjad.attach(abjad.Dynamic("pp"), staff[2][0])
                abjad.attach(abjad.Dynamic("p"), staff[3][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[5][-1])

                abjad.attach(abjad.Dynamic("p"), staff[7][2])
                abjad.attach(abjad.Dynamic("ppp"), staff[8][0])
                abjad.attach(abjad.Dynamic("p"), staff[8][4])

                abjad.attach(abjad.Dynamic("pp"), staff[9][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[12][0])
                abjad.attach(abjad.Dynamic("p"), staff[14][0])

                abjad.attach(abjad.Articulation("tenuto"), staff[1][2])
                abjad.attach(abjad.Articulation("tenuto"), staff[1][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[1][4])

                abjad.attach(abjad.Articulation("tenuto"), staff[5][4])
                abjad.attach(abjad.Articulation("tenuto"), staff[6][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[9][1])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][3])

                abjad.attach(abjad.Dynamic("ppp"), staff[17][-1])

            elif instr == "cello":
                abjad.attach(abjad.Dynamic("ppp"), staff[0][2])
                abjad.attach(abjad.StartHairpin(), staff[0][2])
                abjad.attach(abjad.Dynamic("p"), staff[1][1])
                abjad.attach(abjad.StartHairpin(">"), staff[1][1])
                abjad.attach(abjad.Dynamic("pp"), staff[2][0])
                abjad.attach(abjad.Dynamic("p"), staff[3][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[6][0])

                abjad.attach(abjad.Dynamic("p"), staff[7][1])
                abjad.attach(abjad.Dynamic("ppp"), staff[8][0])
                abjad.attach(abjad.Dynamic("p"), staff[8][4])

                abjad.attach(abjad.Dynamic("pp"), staff[9][1])
                abjad.attach(abjad.Dynamic("p"), staff[14][0])

                abjad.attach(abjad.Articulation("tenuto"), staff[1][1])
                abjad.attach(abjad.Articulation("tenuto"), staff[1][2])
                abjad.attach(abjad.Articulation("tenuto"), staff[1][3])

                abjad.attach(abjad.Articulation("tenuto"), staff[5][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[5][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[6][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[6][3])
                abjad.attach(abjad.Articulation("tenuto"), staff[9][1])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][0])
                abjad.attach(abjad.Articulation("tenuto"), staff[10][3])

                abjad.attach(abjad.Dynamic("ppp"), staff[17][-1])

    return verse
