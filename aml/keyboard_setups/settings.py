# map physical output name to particular channel.
# can be changed dynamically before program start if new setup requires different mapping.
PHYSICAL_OUTPUT2CHANNEL_MAPPING = {
    # radios or other loudspeakers with a strong filter
    "radio_ll": 0,
    "radio_lr": 1,
    "radio_rl": 2,
    "radio_rr": 3,
    # transducers that have been attached on the instruments
    "violin": 4,
    "viola": 5,
    "cello": 6,
    # usual keyboard amplifier
    "pianoteq": 7,
}


INPUT2INSTRUMENT_MAPPING = {
    # dpa microphones
    "violin": 0,
    "viola": 1,
    "cello": 2,
    # virtual mapping from modarrt standalone pianoteq to pyo input
    "pianoteq": 3,
}


SIMULATION_PATH = "simulations"

INPUT2SIMULATION_PATH_MAPPING = {
    instr: "{}/{}.wav".format(SIMULATION_PATH, instr)
    for instr in ("violin", "viola", "cello")
}


# the next dict describes the real positions where the string players are placed on the
# stage where 0 is very left, 1 is left-right, 2 is right-left and 3 is very right
STRING_INSTRUMENT2ROOM_POSITION = {"violin": 0, "cello": 1, "viola": 3}


TRACK2MIXER_NUMBER_MAPPING = {
    "sine_violin": 0,
    "sine_viola": 1,
    "sine_cello": 2,
    "pianoteq": 3,
    "gong_ll": 4,
    "gong_lr": 5,
    "gong_rl": 6,
    "gong_rr": 7,
    "strings_ll": 8,
    "strings_lr": 9,
    "strings_rl": 10,
    "strings_rr": 11,
}

SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING = {"violin": 0, "viola": 1, "cello": 2}

GONG_MIXER2CHANNEL_MAPPING = {
    "radio_ll": 0,
    "radio_lr": 1,
    "radio_rl": 2,
    "radio_rr": 3,
}

STRING_MIXER2CHANNEL_MAPPING = {
    "radio_ll": 0,
    "radio_lr": 1,
    "radio_rl": 2,
    "radio_rr": 3,
}


KORG_NANOCONTROL2CONTROL_NUMBER = {
    "slider11": 2,
    "slider12": 3,
    "slider13": 4,
    "slider14": 5,
    "slider16": 8,
    "slider17": 9,
    "slider18": 12,
    "slider19": 13,
    "slider21": 42,
    "slider22": 43,
    "slider23": 50,
    "slider24": 51,
    "slider25": 52,
    "slider26": 53,
    "slider27": 54,
    "slider28": 55,
    "slider29": 56,
}
