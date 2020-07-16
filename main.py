if __name__ == "__main__":
    """
    from mu.utils import infit

    from aml import globals_
    from aml import versemaker
    from aml.trackmaker import keyboard
    from aml.trackmaker import strings

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
    #     59,
    #     15,
    #     tempo_factor=0.35,
    #     octave_of_first_pitch=0,
    #     harmonic_tolerance=0.3,
    #     ro_temperature=0.6,
    #     ro_density=0.685,
    # )
    # vm.remove_area(11, len(vm.bars))
    # vm.repeat_area(0, 4)

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

    # vm.attach(
    #     violin=strings.SimpleStringMaker(globals_.VIOLIN),
    #     viola=strings.SimpleStringMaker(globals_.VIOLA),
    #     cello=strings.SimpleStringMaker(
    #         globals_.CELLO,
    #         tremolo_maker=infit.ActivityLevel(0),
    #         shall_add_optional_pitches=True,
    #     ),
    #     keyboard=keyboard.KeyboardMaker(),
    # )

    from aml import transcriptions
    import fractions

    time_transcriber = transcriptions.TimeTranscriber(
        post_stretch_factor=fractions.Fraction(1, 1)
    )

    acciaccatura_maker = infit.ActivityLevel(4)

    vm = versemaker.VerseMaker(
        59,
        10,
        tempo_factor=0.3,
        octave_of_first_pitch=-1,
        harmonic_tolerance=0.8,
        ro_temperature=0.7,
        ro_density=0.685,
        time_transcriber=time_transcriber,
    )

    harmonic_pitches_activity = 0.3
    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            harmonic_pitches_activity=harmonic_pitches_activity,
            acciaccatura_maker=acciaccatura_maker,
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            harmonic_pitches_activity=harmonic_pitches_activity,
            acciaccatura_maker=acciaccatura_maker,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            harmonic_pitches_activity=harmonic_pitches_activity,
            acciaccatura_maker=acciaccatura_maker,
            tremolo_maker=infit.ActivityLevel(1),
        ),
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
        # chapters.Chapter.from_path("{}/an-nuh".format(globals_.COMPOSITION_PATH)),
    )

    # render chapters
    # [ch(render_each_instrument=False, render_verses=False) for ch in chap]
    [ch(render_each_instrument=False, render_verses=True) for ch in chap]
    # [ch(render_each_instrument=True, render_verses=True) for ch in chap]

    # render introduction

    # making partbooks
