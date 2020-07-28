import quicktions as fractions

from mu.utils import infit

from mutools import lily

from aml import globals_
from aml import versemaker

from aml.trackmaker import keyboard
from aml.trackmaker import strings


#####################################################
#            post processing functions              #
#####################################################

def _adapt_violin(violin: lily.NOventLine) -> None:
    pass


def _adapt_viola(viola: lily.NOventLine) -> None:
    pass


def _adapt_cello(cello: lily.NOventLine) -> None:
    pass


def _adapt_keyboard(left: lily.NOventLine, right: lily.NOventLine) -> None:
    pass


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        'closing',
        tempo_factor=0.28,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.485,
        ro_temperature=0.61,
        ro_density=0.684,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.25, 0.1),
        area_density_reference_size=fractions.Fraction(1, 2),
        area_min_split_size=fractions.Fraction(1, 4),
    )

    # vm.remove_area(0, 2)
    # vm.remove_area(16, 19)
    # vm.remove_area(33, 35)

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            tremolo_maker=infit.ActivityLevel(0),
            acciaccatura_maker=infit.ActivityLevel(1),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2)),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.6,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=fractions.Fraction(3, 16),
            optional_pitches_density=0.25,
            after_glissando_size=fractions.Fraction(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(5, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(0),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.4,
            harmonic_pitches_density=0.45,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=fractions.Fraction(3, 16),
            optional_pitches_density=0.25,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(0),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2)),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(0),
            harmonic_pitches_activity=0.35,
            harmonic_pitches_density=0.5,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=fractions.Fraction(3, 16),
            optional_pitches_density=0.3,
        ),
        keyboard=keyboard.KeyboardMaker(),
    )

    _adapt_violin(vm.violin.musdat[1])
    _adapt_viola(vm.viola.musdat[1])
    _adapt_cello(vm.cello.musdat[1])
    _adapt_keyboard(vm.keyboard.musdat[2], vm.keyboard.musdat[1])

    verse = vm()

    return verse
