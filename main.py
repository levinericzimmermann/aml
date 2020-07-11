if __name__ == "__main__":
    from aml import globals_
    from aml import versemaker
    from aml.trackmaker import keyboard
    from aml.trackmaker import strings

    vm = versemaker.VerseMaker(
        # 71, 21, tempo_factor=0.35, octave_of_first_pitch=0, harmonic_tolerance=0.385
        59,
        # "opening",
        5,
        tempo_factor=0.3,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.35,
        # harmonic_tolerance=0.375,
        ro_temperature=0.7,
        # ro_temperature=0.65,
        # ro_density=0.45,
    )

    vm.attach(
        violin=strings.SimpleStringMaker(globals_.VIOLIN),
        viola=strings.SimpleStringMaker(globals_.VIOLA),
        cello=strings.SimpleStringMaker(globals_.CELLO),
        keyboard=keyboard.KeyboardMaker(),
    )

    verse = vm()

    verse.notate("tests/first/sco/verse")
    verse.cello.notate("tests/first/sco/cello")
    verse.viola.notate("tests/first/sco/viola")
    verse.violin.notate("tests/first/sco/violin")
    verse.keyboard.notate("tests/first/sco/keyboard")

    verse.keyboard.synthesize("tests/first/sf/keyboard")
    verse.viola.synthesize("tests/first/sf/viola")
    verse.cello.synthesize("tests/first/sf/cello")
    verse.violin.synthesize("tests/first/sf/violin")

    """
    from aml import chapters
    from aml import globals_

    # defining chapters
    chap = (
        chapters.Chapter.from_path("{}/al-hasyr".format(globals_.COMPOSITION_PATH)),
        chapters.Chapter.from_path("{}/an-nuh".format(globals_.COMPOSITION_PATH)),
    )

    # render chapters
    [ch() for ch in chap]

    # render introduction

    # making partbooks
    """
