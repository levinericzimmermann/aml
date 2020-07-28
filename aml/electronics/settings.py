"""This file contains all global settings.

Depending on the performance situation its values could be adapted.
"""

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

PHYSICAL_OUTPUT2STEREO_PANNING = {
    # radios or other loudspeakers with a strong filter
    "radio_ll": 0,
    "radio_lr": 0.3333,
    "radio_rl": 0.6666,
    "radio_rr": 1,
    # transducers that have been attached on the instruments
    "violin": 0,
    "viola": 1,
    "cello": 0.7,
    # usual keyboard amplifier
    "pianoteq": 0.4,
}
PHYSICAL_OUTPUT2STEREO_PANNING = {
    name: (PHYSICAL_OUTPUT2CHANNEL_MAPPING[name], PHYSICAL_OUTPUT2STEREO_PANNING[name])
    for name in PHYSICAL_OUTPUT2STEREO_PANNING
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
    # item-scene-strip: (channel, control number)
    "slider11": (1, 1),
    "slider12": (1, 2),
    "slider13": (1, 3),
    "slider14": (1, 4),
    "slider15": (1, 5),
    # "slider16": (1, 6),  # somehow can't be detected
    "slider17": (1, 7),
    "slider18": (1, 8),
    "slider19": (1, 9),
    "slider21": (1, 10),
    "slider22": (1, 11),
    "slider23": (1, 12),
    "slider24": (1, 13),
    "slider25": (1, 14),
    "slider26": (1, 15),
    "slider27": (1, 16),
    "slider28": (1, 17),
    "slider29": (1, 18),
    "slider31": (1, 19),
    "slider32": (1, 20),
    "slider33": (1, 21),
    "slider34": (1, 22),
    "slider35": (1, 23),
    "slider36": (1, 24),
    "slider37": (1, 25),
    "slider38": (1, 26),
    "slider39": (1, 27),
    "knob11": (1, 37),
    # "knob12": (1, 38),  # somehow can't be detected
    "knob13": (1, 39),
    "knob14": (1, 40),
    "knob15": (1, 41),
    "knob16": (1, 42),
    "knob17": (1, 43),
    "knob18": (1, 44),
    "knob19": (1, 45),
    "knob21": (1, 46),
    "knob22": (1, 47),
    "knob23": (1, 48),
    "knob24": (1, 49),
    "knob25": (1, 50),
    "knob26": (1, 51),
    "knob27": (1, 52),
    "knob28": (1, 53),
    "knob29": (1, 54),
    "knob31": (1, 55),
    "knob32": (1, 56),
    "knob33": (1, 57),
    "knob34": (1, 58),
    "knob35": (1, 59),
    "knob36": (1, 60),
    "knob37": (1, 61),
    "knob38": (1, 62),
    "knob39": (1, 63),
    "button111": (1, 73),
    "button112": (1, 74),
    "button121": (1, 75),
    "button122": (1, 76),
    "button131": (1, 77),
    "button132": (1, 78),
    "button141": (1, 79),
    "button142": (1, 80),
    "button151": (1, 81),
    "button152": (1, 82),
    "button161": (1, 83),
    "button162": (1, 84),
    "button171": (1, 85),
    "button172": (1, 86),
    "button181": (1, 87),
    "button182": (1, 88),
    "button191": (1, 89),
    "button192": (1, 90),
    "button211": (1, 91),
    "button212": (1, 92),
    "button221": (1, 93),
    "button222": (1, 94),
    "button231": (1, 95),
    # "button232": (1, 96),  # somehow couldn't be dected
    # "button241": (1, 97),
    # "button242": (1, 98),
    # "button251": (1, 99),
    # "button252": (1, 100),
    # "button261": (1, 101),
    "button262": (1, 102),
    "button271": (1, 103),
    "button272": (1, 104),
    "button281": (1, 105),
    "button282": (1, 106),
    "button291": (1, 107),
    "button292": (1, 108),
    "button311": (1, 109),
    "button312": (1, 110),
    "button321": (1, 111),
    "button322": (1, 112),
    "button331": (1, 113),
    "button332": (1, 114),
    "button341": (1, 115),
    "button342": (1, 116),
    "button351": (1, 117),
    "button352": (1, 118),
    "button361": (1, 119),
    # "button362": (1, 120),  # strange outputs
    # "button371": (1, 121),
    # "button372": (1, 122),
    # "button381": (1, 123),
    # "button382": (1, 124),
    # "button391": (1, 125),
    # "button392": (1, 126),
    "previous": (1, 28),
    "next": (1, 30),
    "play": (1, 29),
    "rewind": (1, 31),
    "stop": (1, 32),
    "record": (1, 33),
}

KORG_NANOCONTROL_STRIP2CONTROLLED_SIGNAL = {
    1: "master_out",
    2: "strings",
    3: "gong",
    4: "pianoteq",
    5: "transducer",
    6: "gamelan",
    7: "tape",
}

CONTROLLED_SIGNAL2KORG_NANOCONTROL_STRIP = {
    name: strip_number
    for strip_number, name in KORG_NANOCONTROL_STRIP2CONTROLLED_SIGNAL.items()
}

# deciding whether the upper button is mutting the strip / making it solo or if the lower
# button is mutting it / making it solo.
SOLO_BUTTON, MUTE_BUTTON = 1, 2

CONTROLLED_SIGNAL_SCENE = 2
