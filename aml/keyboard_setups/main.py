if __name__ == "__main__":
    import argparse

    import pyo

    import midi
    import settings
    import strings
    import pianoteq

    # adding possibility for testing the program with stereo mode and with stings
    # simulation.
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--simulation", type=bool, default=False)
    PARSER.add_argument("--stereo", type=bool, default=False)
    PARSED_ARGS = PARSER.parse_args()
    USE_SIMULATION = PARSED_ARGS.simulation
    USE_STEREO = PARSED_ARGS.stereo

    if USE_STEREO:
        settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING = {
            "radio_ll": 0,
            "radio_lr": 1,
            "radio_rl": 0,
            "radio_rr": 1,
            "violin": 0,
            "viola": 1,
            "cello": 0,
            "pianoteq": 1,
        }

    SERVER = pyo.Server(
        audio="jack",
        midi="jack",
        nchnls=len(settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING),
        buffersize=512,
    )

    # listening / sending to all midi output devices
    SERVER.setMidiInputDevice(99)
    SERVER.setMidiOutputDevice(99)

    # starting server
    SERVER.boot()

    # making final mixer
    MIXER = pyo.Mixer(outs=8, chnls=1)
    MIXER.ctrl(title="master-out")

    # getting inputs
    if USE_SIMULATION:
        INPUTS = {
            instrument: pyo.SfPlayer(path).play()
            for instrument, path in settings.INPUT2SIMULATION_PATH_MAPPING.items()
        }
        INPUTS.update({"pianoteq": pyo.Input(3)})
    else:
        INPUTS = {
            instrument: pyo.Input(channel).play()
            for instrument, channel in settings.INPUT2INSTRUMENT_MAPPING.items()
        }

    # sending pianoteq to mixer
    MIXER.addInput(settings.TRACK2MIXER_NUMBER_MAPPING["pianoteq"], INPUTS["pianoteq"])
    MIXER.setAmp(
        settings.TRACK2MIXER_NUMBER_MAPPING["pianoteq"],
        settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING["pianoteq"],
        1,
    )

    # generating midi synthesizer for keyboard player
    MIDI_SYNTH = midi.MidiSynth()
    MIDI_SYNTH.notes.keyboard()

    # making string - input analysis objects
    STRINGS = {
        instrument: strings.String(signal)
        for instrument, signal in INPUTS.items()
        if instrument != "pianoteq"
    }

    STRING_PROCESSER = strings.StringProcesser(STRINGS, MIDI_SYNTH)

    ###############################################################################
    #                       adding signals to master out                          #
    ###############################################################################

    # adding strings sounds to mixer
    for (
        physical_output,
        string_mixer_channel,
    ) in settings.STRING_MIXER2CHANNEL_MAPPING.items():
        track_mixer_number = (
            settings.TRACK2MIXER_NUMBER_MAPPING[
                "strings_{}".format(physical_output.split("_")[1])
            ],
        )
        MIXER.addInput(
            track_mixer_number, STRING_PROCESSER.strings_mixer[string_mixer_channel][0],
        )
        MIXER.setAmp(
            track_mixer_number,
            settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[physical_output],
            1,
        )

    # adding transducer sounds to mixer
    for (
        instrument,
        sine_mixer_channel,
    ) in settings.SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING.items():
        track_mixer_number = (
            settings.TRACK2MIXER_NUMBER_MAPPING["sine_{}".format(instrument)],
        )
        MIXER.addInput(
            track_mixer_number, MIDI_SYNTH.sine_mixer[sine_mixer_channel][0],
        )
        MIXER.setAmp(
            track_mixer_number, settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[instrument], 1
        )

    # adding gong sounds to mixer
    for (
        physical_output,
        gong_mixer_channel,
    ) in settings.GONG_MIXER2CHANNEL_MAPPING.items():
        track_mixer_number = (
            settings.TRACK2MIXER_NUMBER_MAPPING[
                "gong_{}".format(physical_output.split("_")[1])
            ],
        )
        MIXER.addInput(
            track_mixer_number, MIDI_SYNTH.gong_mixer[gong_mixer_channel][0],
        )
        MIXER.setAmp(
            track_mixer_number,
            settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[physical_output],
            1,
        )

    # making pianoteq modulation object
    PTEQ_MODULATOR = pianoteq.Modulator(MIDI_SYNTH.pianoteq_trigger, SERVER)

    # adding pianoteq volume controler gui
    INPUTS["pianoteq"].ctrl([pyo.SLMapMul()], title="pianoteq")

    # sending everything from the mixer to physical outputs
    [MIXER[i][0].out(i) for i in settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING.values()]

    # starting gui
    SERVER.start()
    SERVER.gui(locals(), title="aml", exit=True)
