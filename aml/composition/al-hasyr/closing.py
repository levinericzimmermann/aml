from mutools import attachments

from mu.utils import infit

from aml import globals_
from aml import versemaker
from aml.trackmaker import keyboard
from aml.trackmaker import strings


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        "closing",
        tempo_factor=0.28,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.59,
        ro_temperature=0.65,
        ro_density=0.685,
    )
    vm.remove_area(0, 1)
    # vm.remove_area(11, len(vm.bars))

    vm.verse = "6"

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            acciaccatura_maker=infit.ActivityLevel(1),
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(7),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.5,
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(4),
            acciaccatura_maker=infit.ActivityLevel(1),
            pizz_maker=infit.ActivityLevel(10),
            harmonic_pitches_activity=0.3,
            harmonic_pitches_density=0.5,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            shall_add_optional_pitches=False,
            acciaccatura_maker=infit.ActivityLevel(2),
            pizz_maker=infit.ActivityLevel(7),
            harmonic_pitches_activity=0.2,
            harmonic_pitches_density=0.5,
        ),
        keyboard=keyboard.KeyboardMaker(),
    )

    # vm.viola.musdat[1][-2].string_contact_point = attachments.StringContactPoint(
    #     "pizzicato"
    # )

    return vm()
