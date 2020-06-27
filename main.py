if __name__ == "__main__":
    import abjad
    from aml import versemaker
    from aml.trackmaker import keyboard
    from aml.trackmaker import strings

    vm = versemaker.VerseMaker(
        # 71, 21, tempo_factor=0.35, octave_of_first_pitch=0, harmonic_tolerance=0.385
        59,
        "opening",
        # 71,
        # 10,
        tempo_factor=0.35,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.385,
    )

    vm.attach(
        violin=strings.SimpleStringMaker(abjad.Violin()),
        viola=strings.SimpleStringMaker(abjad.Viola()),
        cello=strings.SimpleStringMaker(abjad.Cello()),
        keyboard=keyboard.KeyboardMaker(),
    )

    verse = vm()

    verse.notate("tests/first/sco/verse")
    verse.cello.notate("tests/first/sco/cello")
    verse.violin.notate("tests/first/sco/violin")
    verse.keyboard.notate("tests/first/sco/keyboard")

    verse.keyboard.synthesize("tests/first/sf/keyboard")
    verse.viola.synthesize("tests/first/sf/viola")
    verse.violin.synthesize("tests/first/sf/violin")

    # from aml import transcriptions

    # trans = transcriptions.QiroahTranscription.from_complex_scale(verse=1)
    # transformation = transcriptions.ComplexMeterTranscriber._available_metrical_loops[
    #     5
    # ].transform_melody(trans)
    # print(transformation[0])
    # print("dur:", transformation[0].duration)
    # print("metricity:", transformation[1])
    # print("deviation:", transformation[2])

    # print(trans)
    # print("")
    # print(trans.bars)

    # best = transcriptions.ComplexMeterTranscriber().estimate_best_meter(trans)
    # for item in best:
    #     print(item)
    #     print("")

    # b0 = transcriptions.Bar((3, 4))
    # print(b0)
    # print(b0.get_pulse_rhythm_and_metricity_per_beat(15))

    # import abjad
    # ml = transcriptions.MetricalLoop(
    #     (3, 4, 5),
    #     transcriptions.Bar(abjad.TimeSignature((5, 4))),
    #     transcriptions.Bar(abjad.TimeSignature((3, 4))),
    #     transcriptions.Bar(abjad.TimeSignature((4, 4))),
    # )

    # for prime in (3, 4, 5):
    #     print(tuple(ml.get_rhythm_and_metricity_per_prime()[prime][0]))

    # print(transcriptions.ComplexMeterTranscriber._available_metrical_loops)

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
