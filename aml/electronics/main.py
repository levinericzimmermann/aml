"""Live electronic program for 'kagem Karina'.

May be started with 'python3 main.py'.
The program can be exited through stoping and exiting the pyo server gui.

Different flags can be added when starting the program:

    --channels
        str {mono, stereo, quadraphonic, multichannel}
        default: multichannel

    --keyboard
        bool
        default: False

    --logging
        bool
        default: True

    --simulation
        str {opening, 1, 5, closing}
        default: None

    --spectrum
        bool
        default: False
"""

if __name__ == "__main__":
    import argparse
    import logging
    import subprocess
    import time

    import mido

    import pyo

    import cues
    import loclog
    import mixing
    import pianoteq
    import settings
    import spat
    import strings

    # adding possibility for testing the program with stereo mode and with stings
    # simulation.
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--simulation", type=str, default=None)
    PARSER.add_argument("--channels", type=str, default="multichannel")
    PARSER.add_argument("--logging", type=bool, default=True)
    PARSER.add_argument("--keyboard", type=bool, default=False)
    PARSER.add_argument("--spectrum", type=bool, default=False)
    PARSED_ARGS = PARSER.parse_args()
    SIMULATION_VERSE = PARSED_ARGS.simulation
    CHANNELS = PARSED_ARGS.channels
    SHOW_LOGGING = PARSED_ARGS.logging
    ADD_KEYBOARD = PARSED_ARGS.keyboard
    ADD_SPECTRUM = PARSED_ARGS.spectrum

    # start performance mode
    subprocess.run("performance_on.sh", shell=True)

    # start jack
    subprocess.run("qjackctl -a patchbay-new.xml -s &", shell=True)
    time.sleep(0.5)

    # start pianoteq
    PIANOTEQ_PROCESS = subprocess.Popen(
        [
            "pianoteq",
            # basic preset average Harp
            "--preset",
            "Concert Harp Daily",
            # tuning fxp
            "--fxp",
            "aml.fxp",
            # keyboard / velocity fxp
            "--fxp",
            "standard-velocity.mfxp",
            # set midimapping
            "--midimapping",
            "complete",
            # increase performance
            "--multicore",
            "max",
        ]
    )
    time.sleep(2)

    # start htop
    HTOP_LOGGER = loclog.HtopLogger()

    with open(settings.MIDI_CONTROL_LOGGING_FILE, "w") as f:
        f.write("RECEIVED-MIDI-CONTROL-MESSAGES\n")

    if SHOW_LOGGING:
        logging.basicConfig(level=logging.INFO)

    SERVER = pyo.Server(
        audio="jack", midi="jack", nchnls=len(settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING),
    )

    # listening / sending to all midi output devices
    SERVER.setMidiInputDevice(99)
    SERVER.setMidiOutputDevice(99)

    # starting server
    SERVER.boot()

    import gender_player
    import midi

    # making final mixer
    MIXER = pyo.Mixer(outs=8, chnls=1)

    logging.info("getting inputs")
    if SIMULATION_VERSE:
        VERSE_PATH = "{}/{}".format(settings.SIMULATION_PATH, SIMULATION_VERSE)
        INPUTS = {
            instrument: pyo.SfPlayer(
                "{}/{}/synthesis.wav".format(VERSE_PATH, instrument), mul=0.7,
            )
            for instrument, _ in settings.INPUT2INSTRUMENT_MAPPING.items()
            if instrument != "pianoteq"
        }
        INPUTS.update({"pianoteq": pyo.Input(3)})

    else:
        INPUTS = {
            instrument: pyo.Input(channel).play()
            for instrument, channel in settings.INPUT2INSTRUMENT_MAPPING.items()
        }

    logging.info("adding meter for inputs")
    INPUT_METER = loclog.Meter(*INPUTS.items())

    logging.info("sending pianoteq to mixer")
    MIXER.addInput(settings.TRACK2MIXER_NUMBER_MAPPING["pianoteq"], INPUTS["pianoteq"])
    MIXER.setAmp(
        settings.TRACK2MIXER_NUMBER_MAPPING["pianoteq"],
        settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING["pianoteq"],
        1,
    )

    logging.info("generating midi synthesizer for keyboard player")

    MIDI_DATA_LOGGER = loclog.MidiDataLogger()
    MIDI_SYNTH = midi.MidiSynth(SERVER, MIDI_DATA_LOGGER)

    if ADD_KEYBOARD:
        MIDI_SYNTH.notes.keyboard()

    ###############################################################################
    #                   making live-electronic modules & cues                     #
    ###############################################################################

    logging.info("generating live electronic modules")

    BALANCED_SPAT_MAKER = spat.BalancedSpatMaker(
        [
            MIXER[settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[physical_output]][0]
            for physical_output in ("radio_ll", "radio_lr", "radio_rl", "radio_rr")
        ]
    )

    STRINGS = {
        instrument: strings.String(signal)
        for instrument, signal in INPUTS.items()
        if instrument != "pianoteq"
    }

    STRING_PROCESSER = strings.StringProcesser(STRINGS, MIDI_SYNTH)
    GENDER_PLAYER = gender_player.GenderPlayer(STRINGS, MIDI_SYNTH, BALANCED_SPAT_MAKER)

    CUE_ORGANISER = cues.CueOrganiser((STRING_PROCESSER, GENDER_PLAYER))

    # add cues
    CUE_ORGANISER.append(cues.Cue(strings={}, gender_sample_player={}))
    CUE_ORGANISER.append(cues.Cue())
    CUE_ORGANISER.append(cues.Cue(strings={}))

    ###############################################################################
    #                       adding signals to master out                          #
    ###############################################################################

    logging.info("adding live electronic modules")
    CUE_ORGANISER.add_modules_to_mixer(MIXER)

    logging.info("adding transducer sounds to mixer")
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

    for (
        physical_output,
        sine_mixer_channel,
    ) in settings.SINE_TO_RADIO_MIXER_INSTRUMENT2CHANNEL_MAPPING.items():
        track_mixer_number = (
            settings.TRACK2MIXER_NUMBER_MAPPING[
                "sine_{}".format(physical_output.split("_")[1])
            ],
        )
        MIXER.addInput(
            track_mixer_number, MIDI_SYNTH.sine_radio_mixer[sine_mixer_channel][0],
        )
        MIXER.setAmp(
            track_mixer_number,
            settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[physical_output],
            1,
        )

    logging.info("adding gong sounds to mixer")
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

    logging.info("making pianoteq modulation object")
    PTEQ_MODULATOR = pianoteq.Modulator(MIDI_SYNTH.pianoteq_trigger, SERVER)

    logging.info("sending everything from the mixer to physical outputs")
    if CHANNELS == "multichannel":
        [MIXER[i][0].out(i) for i in settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING.values()]

    elif CHANNELS == "quadraphonic":
        [MIXER[i][0].play() for i in settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING.values()]
        PANNER = [
            pyo.Pan(signal[0], outs=4, pan=[0, 0.35, 0.65, 1][i]).out()
            for signal, i in zip(
                MIXER, settings.PHYSICAL_OUTPUT2QUADRAPHONIC_PANNING.values()
            )
        ]

    elif CHANNELS == "stereo":
        [MIXER[i][0].play() for i in settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING.values()]
        PANNER = [
            pyo.Pan(MIXER[data[0]][0], outs=2, pan=data[1]).out()
            for data in settings.PHYSICAL_OUTPUT2STEREO_PANNING.values()
        ]

    elif CHANNELS == "mono":
        [MIXER[i][0].out(0) for i in settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING.values()]

    else:
        msg = "Unknown channels option {}.".format(CHANNELS)
        raise NotImplementedError(msg)

    MIXSYSTEM = mixing.MixSystem(
        ("master_out", (MIXER, 0, 0.5, "slider")),
        ("strings", (STRING_PROCESSER.mixer, 0, 1, "slider")),
        ("gong", (MIDI_SYNTH.gong_mixer, 0, 2, "slider")),
        ("pianoteq", (INPUTS["pianoteq"], 0, 6, "slider")),
        # right hand output to radios
        ("transducer", (MIDI_SYNTH.sine_radio_mixer, 0, 0.25, "slider")),
        # right hand output to transducer
        ("transducer", (MIDI_SYNTH.sine_mixer, 0, 0.35, "knob")),
        # samples triggered by string onsets
        ("gender_player", (GENDER_PLAYER.mixer, 0, 1, "slider")),
    )

    # WORKS ONLY WITH PORTMIDI, BUT NOT WITH JACKMIDI! TODO(add possibility to list
    # midi devices with jack-midi)
    # if SHOW_LOGGING:
    #     logging.info("Found midi devices...")
    #     pyo.pm_list_devices()

    logging.info("starting server & gui")
    SERVER.start()

    if SIMULATION_VERSE:
        _RUN_SIMULATION = True
        for instr, signal in INPUTS.items():
            if instr != "pianoteq":
                INPUTS[instr] = signal.play(delay=0.244)
                track_mixer_number = settings.TRACK2MIXER_NUMBER_MAPPING[
                    "{}_simulation".format(instr)
                ]
                MIXER.addInput(
                    track_mixer_number, INPUTS[instr],
                )
                MIXER.setAmp(
                    track_mixer_number,
                    settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[
                        "radio_{}".format(
                            ("ll", "lr", "rl", "rr")[
                                settings.STRING_INSTRUMENT2ROOM_POSITION[instr]
                            ]
                        )
                    ],
                    settings.STRING_SIMULATION_VOLUME,
                )

        import threading

        def _play_midi_file():
            for message in mido.MidiFile(
                "{}/keyboard/keyboard_simulation.midi".format(VERSE_PATH)
            ).play():
                if not _RUN_SIMULATION:
                    break
                SERVER.addMidiEvent(*message.bytes())

        MIDI_PLAYER = threading.Thread(target=_play_midi_file)
        MIDI_PLAYER.start()

    if ADD_SPECTRUM:
        SPECTRUM = pyo.Spectrum(sum((m[0] for m in MIXER)), wintitle="MIXED")

    SERVER.gui(locals(), title="aml", exit=False)

    INPUT_METER.close()
    MIDI_DATA_LOGGER.close()
    HTOP_LOGGER.close()
    CUE_ORGANISER.close()

    PIANOTEQ_PROCESS.terminate()

    if SIMULATION_VERSE:
        _RUN_SIMULATION = False
        MIDI_PLAYER.join(0)

    subprocess.run("performance_off.sh", shell=True)
