from mu.utils import infit

from aml import globals_
from aml import versemaker
from aml.trackmaker import keyboard
from aml.trackmaker import strings


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        5,
        tempo_factor=0.28,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.49,
        ro_temperature=0.7,
        ro_density=0.685,
    )
    vm.remove_area(0, 2)
    vm.remove_area(17, len(vm.bars))

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            acciaccatura_maker=infit.ActivityLevel(1),
            tremolo_maker=infit.ActivityLevel(2),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.6,
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(4),
            acciaccatura_maker=infit.ActivityLevel(0),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.55,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(2),
            harmonic_pitches_activity=0.2,
            harmonic_pitches_density=0.5,
        ),
        keyboard=keyboard.KeyboardMaker(),
    )

    return vm()
