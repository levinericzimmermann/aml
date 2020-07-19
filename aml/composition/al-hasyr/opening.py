from mu.utils import infit

from aml import globals_
from aml import versemaker
from aml.trackmaker import keyboard
from aml.trackmaker import strings


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        "opening",
        tempo_factor=0.3,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.35,
        ro_temperature=0.66,
        ro_density=0.7,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.55, 0.2),
    )

    vm.remove_area(0, 2)
    vm.remove_area(15, 17)
    vm.remove_area(29, len(vm.bars))
    vm.repeat_area(2, 6)

    vm.verse = "opening"

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            acciaccatura_maker=infit.ActivityLevel(3),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(5),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.4,
            harmonic_pitches_density=0.6,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            acciaccatura_maker=infit.ActivityLevel(5),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(5),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.4,
            harmonic_pitches_density=0.55,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(3),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(4),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2, 0, 1, 0)),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(9),
            harmonic_pitches_activity=0.45,
            harmonic_pitches_density=0.55,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
        ),
        keyboard=keyboard.KeyboardMaker(),
    )

    return vm()
