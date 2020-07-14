if __name__ == "__main__":
    from mu.utils import infit

    from aml import globals_
    from aml import versemaker
    from aml.trackmaker import keyboard
    from aml.trackmaker import strings

    vm = versemaker.VerseMaker(
        59,
        "opening",
        tempo_factor=0.3,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.35,
        ro_temperature=0.69,
        ro_density=0.7,
        harmonic_pitches_maximum_octave_difference_from_melody_pitch=0,
        area_density_maker=infit.Gaussian(0.35, 0.1),
    )

    vm.remove_area(0, 2)
    vm.remove_area(15, 17)

    # vm = versemaker.VerseMaker(
    #     59,
    #     5,
    #     tempo_factor=0.28,
    #     octave_of_first_pitch=0,
    #     harmonic_tolerance=0.49,
    #     ro_temperature=0.7,
    #     ro_density=0.685,
    # )
    # vm.remove_area(17, len(vm.bars))

    # vm = versemaker.VerseMaker(
    #     71,
    #     14,
    #     tempo_factor=0.225,
    #     octave_of_first_pitch=-1,
    #     harmonic_tolerance=0.4,
    #     ro_temperature=0.585,
    #     ro_density=0.7,
    # )

    # vm = versemaker.VerseMaker(
    #     71,
    #     10,
    #     tempo_factor=0.3,
    #     octave_of_first_pitch=0,
    #     harmonic_tolerance=0.4,
    #     ro_temperature=0.4,
    #     ro_density=0.85,
    # )
    # vm.remove_area(0, 12)

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
