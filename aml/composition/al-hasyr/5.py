import quicktions as fractions

import abjad

from mu.mel import ji

from mu.utils import infit

from mutools import attachments
from mutools import lily

from aml import globals_
from aml import tweaks
from aml import versemaker

from aml.trackmaker import keyboard
from aml.trackmaker import strings


#####################################################
#            post processing functions              #
#####################################################


def _adapt_violin(violin: lily.NOventLine, vm) -> None:
    # violin[3].string_contact_point = attachments.StringContactPoint("pizzicato")
    # violin[3].volume = 2
    # tweaks.add_artifical_harmonic(3, violin[3].pitch[0], violin)
    # violin[3].pitch[0] += ji.r(4, 1)
    # tweaks.add_acciaccatura(
    #     3, ji.r(35, 32), violin, add_glissando=True, use_artifical_harmonic=True
    # )
    # violin[3].volume = 0.1
    tweaks.prolong(3, fractions.Fraction(1, 8), violin)
    # tweaks.swap_duration(2, 3, fractions.Fraction(1, 8), violin)
    previous_duration = fractions.Fraction(violin[6].delay)
    tweaks.split_by_structure(6, 2, violin, vm)
    violin[6].ornamentation = attachments.OrnamentationDown(1)
    violin[6].glissando = None
    difference = previous_duration - violin[7].duration
    violin[7].glissando.pitch_line[0].delay -= difference
    # tweaks.add_acciaccatura(10, ji.r(8, 9), violin, add_glissando=True)
    tweaks.swap_duration(11, 10, fractions.Fraction(7, 32), violin)
    tweaks.add_acciaccatura(11, ji.r(8, 9), violin, add_glissando=True)
    violin[10].string_contact_point = attachments.StringContactPoint("arco")
    violin[11].string_contact_point = attachments.StringContactPoint("arco")
    violin[11].ornamentation = attachments.OrnamentationUp(1)
    tweaks.prolong(12, fractions.Fraction(1, 8), violin)
    tweaks.split(12, violin, fractions.Fraction(1, 8), fractions.Fraction(1, 8))
    # tweaks.rest(10, violin)
    tweaks.prolong(8, fractions.Fraction(1, 32), violin)
    tweaks.change_octave(17, -1, violin)
    # violin[17].tremolo = attachments.Tremolo()
    violin[17].volume = 0.5
    tweaks.add_glissando(17, (0, 0, 1), violin, verse_maker=vm)
    # violin[17].tempo = attachments.Tempo(fractions.Fraction(1, 4), 30)
    tweaks.split(18, violin, fractions.Fraction(1, 16), fractions.Fraction(5, 8))
    violin[19].tempo = attachments.Tempo(fractions.Fraction(1, 4), 40)


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    viola[1].string_contact_point = attachments.StringContactPoint("arco")
    tweaks.add_acciaccatura(3, ji.r(4, 3), viola, add_glissando=True)
    viola[7].acciaccatura = None
    viola[7].ornamentation = attachments.OrnamentationUp(2)
    tweaks.prolong(7, fractions.Fraction(1, 16), viola)
    tweaks.add_glissando(
        7,
        (0, 0, -1),
        viola,
        durations=(fractions.Fraction(3, 8), fractions.Fraction(1, 8)),
    )
    tweaks.change_octave(10, -1, viola)
    viola[14].pitch = [viola[13].pitch[0].copy()]
    viola[14].string_contact_point = attachments.StringContactPoint("arco")
    viola[14].ornamentation = attachments.OrnamentationUp(1)
    tweaks.split_by_structure(14, 2, viola, vm)
    tweaks.rest(14, viola)
    # viola[14].articulation_once = attachments.ArticulationOnce(".")
    tweaks.change_octave(19, 1, viola)

    # tweaks.split(22, viola, fractions.Fraction(3, 8), fractions.Fraction(1, 8))
    viola[22].glissando = None
    tweaks.add_acciaccatura(22, ji.r(35, 24), viola, add_glissando=False)
    tweaks.add_glissando(
        22,
        (0, 0, -1),
        viola,
        durations=(fractions.Fraction(1, 4), fractions.Fraction(1, 8)),
    )
    tweaks.add_glissando(24, (0, -1), viola, verse_maker=vm)
    viola[22].hauptstimme = attachments.Hauptstimme(True, False)
    viola[24].hauptstimme = attachments.Hauptstimme(False, False)
    # tweaks.split(
    #     21,
    #     viola,
    #     fractions.Fraction(1, 8),
    #     fractions.Fraction(1, 2),
    #     fractions.Fraction(1, 8),
    # )
    # viola[23].tempo = attachments.Tempo(fractions.Fraction(1, 4), 30)
    # viola[25].tempo = attachments.Tempo(fractions.Fraction(1, 4), 40)


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    # tweaks.add_glissando(4, (0, 0, 1), cello, verse_maker=vm)
    # cello[3].acciaccatura = None
    cello[3].acciaccatura.add_glissando = True
    tweaks.add_acciaccatura(4, ji.r(8, 15), cello, add_glissando=True)
    tweaks.split_by_structure(5, 2, cello, verse_maker=vm)
    tweaks.rest(5, cello)
    # tweaks.add_acciaccatura(6, ji.r(6, 7), cello, add_glissando=True)
    tweaks.prolong(6, fractions.Fraction(1, 32), cello)
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
    tweaks.prolong(8, fractions.Fraction(5, 16), cello)
    tweaks.split_by_structure(8, 2, cello, verse_maker=vm)
    cello[8].prall = attachments.Prall()
    cello[21].acciaccatura = None
    cello[21].ornamentation = attachments.OrnamentationDown(1)
    cello[23].natural_harmonic = attachments.NaturalHarmonic()
    cello[23].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[23].volume = 1.2
    tweaks.change_octave(23, -1, cello)
    cello[26].string_contact_point = attachments.StringContactPoint("pizzicato")
    cello[26].volume = 1.2
    tweaks.split_by_structure(25, 2, cello, verse_maker=vm)
    cello[25].hauptstimme = attachments.Hauptstimme(True, False)
    cello[26].hauptstimme = attachments.Hauptstimme(False, False)
    tweaks.add_acciaccatura(
        26,
        ji.r(12, 7).register(-2),
        cello,
        use_artifical_harmonic=True,
        add_glissando=False,
    )
    cello[29].optional = None
    tweaks.swap_duration(30, 29, fractions.Fraction(10, 32), cello)
    # cello[28].volume = 0.4
    # cello[28].string_contact_point = attachments.StringContactPoint("arco")
    cello[29].volume = 0.8
    tweaks.split(29, cello, *([fractions.Fraction(1, 8)] * 4))
    cello[30].natural_harmonic = attachments.NaturalHarmonic()
    tweaks.change_octave(31, -1, cello)
    tweaks.swap_duration(32, 31, fractions.Fraction(1, 8), cello)
    tweaks.rest(29, cello)
    # tweaks.split(28, cello, fractions.Fraction(1, 2), fractions.Fraction(1, 8))
    # cello[29].tempo = attachments.Tempo(fractions.Fraction(1, 4), 30)
    # cello[32].tempo = attachments.Tempo(fractions.Fraction(1, 4), 40)
    # cello[28].tremolo = attachments.Tremolo()


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine, vm) -> None:
    # left[3].arpeggio = None
    # left[3].choose = attachments.ChooseOne()
    # left[5].arpeggio = None
    # left[5].choose = attachments.Choose()
    tweaks.shorten(9, fractions.Fraction(3, 16), right)
    tweaks.rest(11, right)
    right[22].pitch = [right[21].pitch[0].copy()]
    right[20].pitch = [right[19].pitch[0].copy()]
    # right[21].tempo = attachments.Tempo(fractions.Fraction(1, 4), 30)
    tweaks.split(
        22,
        right,
        fractions.Fraction(1, 8),
        fractions.Fraction(1, 4),
        fractions.Fraction(3, 8),
    )
    tweaks.rest(23, right)
    # right[23].tempo = attachments.Tempo(fractions.Fraction(1, 4), 40)

    tweaks.split(5, left, fractions.Fraction(1, 16), fractions.Fraction(1, 4))
    tweaks.rest(10, left)
    for n in (21, 20, 19):
        tweaks.rest(n, left)

    tweaks.prolong(18, fractions.Fraction(1, 4), left)
    tweaks.swap_duration(18, 19, fractions.Fraction(1, 32), left)
    tweaks.make_solo_gong(20, left)
    for n in (39, 38, 37, 36):
        tweaks.rest(n, left)

    tweaks.make_solo_gong(35, left)
    tweaks.swap_duration(36, 35, fractions.Fraction(5, 16), left)

    # left[35].tempo = attachments.Tempo(fractions.Fraction(1, 4), 30)
    # left[36].tempo = attachments.Tempo(fractions.Fraction(1, 4), 40)


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        5,
        tempo_factor=0.28,
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
        area_density_reference_size=fractions.Fraction(1, 2),
        area_min_split_size=fractions.Fraction(4, 16),
    )

    vm.remove_area(0, 2)
    vm.remove_area(16, 19)
    # vm.remove_area(32, 34)
    vm.remove_area(28, len(vm.bars))
    vm.repeat_area(2, 10)
    vm.add_bar(10, abjad.TimeSignature((1, 4)))
    vm.repeat_area(11, 12)
    vm.add_bar(11, abjad.TimeSignature((2, 4)))

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
            optional_pitches_min_size=fractions.Fraction(3, 32),
            optional_pitches_avg_size=fractions.Fraction(3, 16),
            optional_pitches_density=0.8,
            after_glissando_size=fractions.Fraction(1, 8),
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
            optional_pitches_min_size=fractions.Fraction(1, 8),
            optional_pitches_avg_size=fractions.Fraction(1, 4),
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
            optional_pitches_min_size=fractions.Fraction(1, 8),
            optional_pitches_avg_size=fractions.Fraction(3, 16),
            optional_pitches_density=0.7,
        ),
        keyboard=keyboard.KeyboardMaker(
            lh_min_metricity_to_add_harmony=0.4,
            lh_min_metricity_to_add_accent=0.8,
            lh_max_metricity_for_arpeggio=0.95,
            lh_min_metricity_to_add_restricted_harmony=0,
            lh_prohibit_repetitions=True,
            lh_add_repetitions_avoiding_notes=True,
            rh_likelihood_making_harmony=0.95,
            harmonies_max_difference=1200,
            harmonies_min_difference=250,
        ),
    )

    _adapt_violin(vm.violin.musdat[1], vm)
    _adapt_viola(vm.viola.musdat[1], vm)
    _adapt_cello(vm.cello.musdat[1], vm)
    _adapt_keyboard(vm.keyboard.musdat[2], vm.keyboard.musdat[1], vm)

    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            nth_line = (2, 1)
        else:
            nth_line = (1,)

        novent_line = getattr(vm, instr).musdat[nth_line[0]]
        novent_line[0].dynamic = attachments.Dynamic("p")

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
            """
            if instr == 'keyboard' and idx[1] == 0:
                abjad.Accidental.respell_with_sharps(staff[1])
                abjad.Accidental.respell_with_flats(staff[7])
                abjad.Accidental.respell_with_flats(staff[8])

            if instr == 'keyboard' and idx[1] == 1:
                abjad.Accidental.respell_with_sharps(staff[11])
            """

    # TODO(ADD METHOD FOR INSERTING NEW BARS -> for the purpose of added rests)

    return verse
