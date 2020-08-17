from quicktions import Fraction as F

# import abjad

# from mu.mel import ji

from mu.utils import infit

from mutools import attachments
from mutools import lily

from aml import globals_
# from aml import tweaks
from aml import versemaker

from aml.trackmaker import keyboard
from aml.trackmaker import strings


#####################################################
#            post processing functions              #
#####################################################


def _adapt_violin(violin: lily.NOventLine, vm) -> None:
    pass


def _adapt_viola(viola: lily.NOventLine, vm) -> None:
    pass


def _adapt_cello(cello: lily.NOventLine, vm) -> None:
    pass


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine, vm) -> None:
    pass


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        4,
        tempo_factor=0.32,
        octave_of_first_pitch=-1,
        harmonic_tolerance=0.7,
        ro_temperature=0.6,
        ro_density=1,
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

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            tremolo_maker=infit.ActivityLevel(0),
            acciaccatura_maker=infit.ActivityLevel(0),
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
            acciaccatura_maker=infit.ActivityLevel(0, start_at=2),
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
            acciaccatura_maker=infit.ActivityLevel(0),
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
            # lh_min_metricity_to_add_harmony=0.4,
            # lh_min_metricity_to_add_accent=0.8,
            # lh_max_metricity_for_arpeggio=0.95,
            # lh_min_metricity_to_add_restricted_harmony=0,
            # lh_prohibit_repetitions=True,
            # lh_add_repetitions_avoiding_notes=True,
            # rh_likelihood_making_harmony=0.95,
            # harmonies_max_difference=1200,
            # harmonies_min_difference=250,
            colotomic_structure=(1, 2, 0, 2),
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

    return verse
