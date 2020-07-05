from aml import versemaker


def main() -> versemaker.Verse:
    import abjad
    from aml import versemaker
    from aml.trackmaker import keyboard
    from aml.trackmaker import strings

    vm = versemaker.VerseMaker(
        59,
        "opening",
        tempo_factor=0.35,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.45,
    )

    vm.attach(
        violin=strings.SimpleStringMaker(abjad.Violin()),
        viola=strings.SimpleStringMaker(abjad.Viola()),
        cello=strings.SimpleStringMaker(abjad.Cello()),
        keyboard=keyboard.KeyboardMaker(),
    )

    verse = vm()
    return verse
