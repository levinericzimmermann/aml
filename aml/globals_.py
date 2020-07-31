import abc
import functools
import numpy as np
import operator
import os

import abjad
import pyo

from mu.mel import ji
from mutools import mus


def _load_scale(idx: int) -> tuple:
    return tuple(
        ji.JIMel.load_json("aml/scale_distribution/pelog_scale_{}.json".format(idx))
    )


def _load_intonations_per_scale_degree() -> tuple:
    intonations_per_scale_degree = []
    for scale_degree in range(7):
        loaded = ji.JIMel.load_json(
            "aml/scale/pelog_scale_degree_{}.json".format(scale_degree)
        )
        intonations_per_scale_degree.append(tuple(sorted(loaded)))

    return tuple(intonations_per_scale_degree)


def _filter_auxiliary_pitches(scale: tuple) -> tuple:
    auxiliary_pitches = (3, 6)
    return tuple(p for idx, p in enumerate(scale) if idx not in auxiliary_pitches)


AVAILABLE_VERSES = tuple(
    (splitted_path[1], splitted_path[2])
    for splitted_path in (
        path[:-4].split("_") for path in os.listdir("aml/transcriptions")
    )
)

RESOLUTION = mus.STANDARD_RESOLUTION


_STRING_VOLUME = 0.7

ORCHESTRATION = mus.Orchestration(
    *tuple(
        mus.MetaTrack(name, n_staves, volume, panning)
        for name, n_staves, volume, panning in (
            ("violin", 3, _STRING_VOLUME * 1.1, 0.185),
            ("viola", 3, _STRING_VOLUME * 1, 0.8),
            ("cello", 3, _STRING_VOLUME * 1.2, 0.65),
            ("keyboard", 3, 2.6, 0.38),
        )
    )
)


INTONATIONS_PER_SCALE_DEGREE = _load_intonations_per_scale_degree()
FILTERED_INTONATIONS_PER_SCALE_DEGREE = _filter_auxiliary_pitches(
    INTONATIONS_PER_SCALE_DEGREE
)

ORIGINAL_SCALE = tuple(
    p.cents for p in ji.JIMel.from_scl("aml/scale/pelog_av.scl", 260)
)[:-1]

FILTERED_ORIGINAL_SCALE = _filter_auxiliary_pitches(ORIGINAL_SCALE)

RATIO2PITCHCLASS = {
    ratio.register(0): pitch
    for ratio, pitch in zip(
        functools.reduce(operator.add, INTONATIONS_PER_SCALE_DEGREE),
        (
            "cxf",
            "c",
            "cxs",
            "dstf",
            "csts",  # instead of "dftf" for avoiding bb when playing artifical harmonic
            "dqf",
            "dxs",  # instead of "efxf",
            "drs",  # instead of "etrf",
            # "dfts",  # instead of "estf",
            "estf",  # undo
            "f",
            "fxs",
            "fqs",
            "gqf",
            "gxf",
            "g",
            # "grs",  # instead of "atrf",
            "atrf",  # undo
            "gfts",  # instead of "astf",
            "aftf",
            "axs",  # instead of "bfxf"
            # "ars",  # instead of "btrf" for avoiding bb when writing artifical harmonic
            "btrf",
            # "as",  # instead of "bf",
            "bf",  # undo
        ),
    )
}


def _mk_midi_pitch2abjad_pitch_tuple() -> tuple:
    # pitch_number2pitch_class = tuple(
    #     abjad.NamedPitchClass(name)
    #     for name in "c df d ef e f gf g af a bf b".split(" ")
    # )
    pitch_number2pitch_class = tuple(
        abjad.NumberedPitchClass(number) for number in range(12)
    )
    midi_pitch2abjad_pitch = tuple(abjad.NamedPitch(n - 60) for n in range(127))
    midi_pitch2abjad_pitch = tuple(abjad.NamedPitch(n - 60) for n in range(127))
    return tuple(
        abjad.NamedPitch(
            name=pitch_number2pitch_class[p.pitch_class.number], octave=p.octave
        )
        for p in midi_pitch2abjad_pitch
    )


MIDI_PITCH2ABJAD_PITCH = _mk_midi_pitch2abjad_pitch_tuple()


RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE = {
    ratio.register(0): pitch
    for ratio, pitch in zip(
        functools.reduce(operator.add, INTONATIONS_PER_SCALE_DEGREE),
        (
            ("fxf", 1),
            ("af", -1),
            ("fxs", 0),
            ("gstf", 0),
            ("ats", -1),  # instead of ("betf", -1) for avoiding bb
            ("gqf", 0),
            ("gxs", 0),  # instead of ("afxf", 0),
            ("bxf", -1),  # insteaf of ("ctrf", 0),
            # ("gfts", 0),  # instead of ("astf", 0),
            ("astf", 0),  # undo
            ("bf", 0),
            ("drf", 0),
            ("bqf", 0),
            ("cqf", 1),
            ("etrf", 0),
            ("c", 1),
            # ("crs", 1),  # instead of ("dtrf", 1),
            ("dtrf", 1),  # undo
            ("etf", 0),  # instead of ("fstf", 0),
            ("dftf", 1),
            ("fxs", 0),  # instead of ("gfxf", 0)
            # ("drs", 1),  # instead of ("etrf", 1)
            ("etrf", 1),  # undo
            # ("ds", 1),  # instead of ("ef", 1),
            ("ef", 1),  # undo
        ),
    )
}

SCALE_PER_INSTRUMENT = {
    instr: tuple(p.normalize() for p in _load_scale(idx))
    for idx, instr in enumerate(("violin", "viola", "cello"))
}

A_CONCERT_PITCH = 442  # a' with 442 Hz
CONCERT_PITCH = A_CONCERT_PITCH / (pow(2, 1 / 12) ** 9)


class _AdaptedInstrument(abc.ABC):
    def __init__(self):
        self._normal_pitches = self._find_pitches(self.normal_pitch_range)
        self._harmonic_pitches = self._find_pitches(self.harmonic_pitch_range)
        self._available_pitches = tuple(
            sorted(self.normal_pitches + self.harmonic_pitches)
        )

    @abc.abstractproperty
    def normal_pitch_range(self) -> tuple:
        raise NotImplementedError

    @abc.abstractproperty
    def harmonic_pitch_range(self) -> tuple:
        raise NotImplementedError

    @abc.abstractproperty
    def artifical_harmonic(self) -> int:
        raise NotImplementedError

    @property
    def scale(self) -> tuple:
        return SCALE_PER_INSTRUMENT[self.name]

    def _find_pitches(self, pitch_range: tuple) -> tuple:
        return tuple(
            sorted(
                functools.reduce(
                    operator.add,
                    (
                        ji.find_all_available_pitches_in_a_specified_range(
                            p, *pitch_range
                        )
                        for p in self.scale
                    ),
                )
            )
        )

    @property
    def normal_pitches(self) -> tuple:
        return self._normal_pitches

    @property
    def harmonic_pitches(self) -> tuple:
        return self._harmonic_pitches

    @property
    def available_pitches(self) -> tuple:
        return self._available_pitches


class _AdaptedCello(abjad.Cello, _AdaptedInstrument):
    normal_pitch_range = (ji.r(1, 4), ji.r(16, 15))
    harmonic_pitch_range = (ji.r(5, 4), ji.r(5, 2))
    artifical_harmonic = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _AdaptedInstrument.__init__(self)


class _AdaptedViola(abjad.Viola, _AdaptedInstrument):
    normal_pitch_range = (ji.r(1, 2), ji.r(32, 15))
    harmonic_pitch_range = (ji.r(2, 1), ji.r(4, 1))
    artifical_harmonic = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _AdaptedInstrument.__init__(self)


class _AdaptedViolin(abjad.Violin, _AdaptedInstrument):
    normal_pitch_range = (ji.r(3, 4), ji.r(3, 1))
    harmonic_pitch_range = (ji.r(3, 1), ji.r(6, 1))
    artifical_harmonic = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _AdaptedInstrument.__init__(self)


CELLO = _AdaptedCello()
VIOLA = _AdaptedViola()
VIOLIN = _AdaptedViolin()


INSTRUMENT_NAME2ADAPTED_INSTRUMENT = {"cello": CELLO, "violin": VIOLIN, "viola": VIOLA}


def _detect_closeness_from_pitch_x_to_pitch_y(
    intonations_per_scale_degree: tuple,
) -> dict:
    closeness_from_pitch_x_to_pitch_y = {}
    harmonicity_net = {}
    for scale_degree_idx, scale_degree0 in enumerate(intonations_per_scale_degree):
        for intonation in scale_degree0:
            intonation = intonation.normalize()
            pitch_harmonicity_pairs = []
            for scale_degree1_idx, scale_degree1 in enumerate(
                intonations_per_scale_degree
            ):
                if scale_degree1_idx != scale_degree_idx:
                    for intonation1 in scale_degree1:
                        intonation1 = intonation1.normalize()
                        harmonicity = (
                            intonation - intonation1
                        ).harmonicity_simplified_barlow
                        pitch_harmonicity_pairs.append((intonation1, harmonicity))
                        harmonicity_net.update(
                            {tuple(sorted((intonation, intonation1))): harmonicity}
                        )
            sorted_pitches = tuple(
                map(
                    operator.itemgetter(0),
                    sorted(
                        pitch_harmonicity_pairs,
                        key=operator.itemgetter(1),
                        reverse=True,
                    ),
                )
            )
            closeness_from_pitch_x_to_pitch_y.update(
                {
                    intonation: {
                        pitch: n
                        for n, pitch in zip(
                            np.linspace(1, 0, len(sorted_pitches), dtype=float),
                            sorted_pitches,
                        )
                    }
                }
            )
    return closeness_from_pitch_x_to_pitch_y, harmonicity_net


CLOSENESS_FROM_PX_TO_PY, HARMONICITY_NET = _detect_closeness_from_pitch_x_to_pitch_y(
    INTONATIONS_PER_SCALE_DEGREE
)


def _make_pitch2scale_degree_dict(intonations_per_scale_degree: tuple) -> dict:
    d = {}
    for sd, pitches in enumerate(intonations_per_scale_degree):
        for into in pitches:
            d.update({into.normalize(): sd})
    return d


def _make_pitch2instrument_dict(scale_per_instrument: dict) -> dict:
    d = {}

    for instr in scale_per_instrument:
        for p in scale_per_instrument[instr]:
            d.update({p.normalize(): instr})

    return d


PITCH2SCALE_DEGREE = _make_pitch2scale_degree_dict(INTONATIONS_PER_SCALE_DEGREE)
PITCH2INSTRUMENT = _make_pitch2instrument_dict(SCALE_PER_INSTRUMENT)


INSTRUMENT_NAME2OBJECT = {
    "cello": abjad.Cello(),
    "violin": abjad.Violin(),
    "viola": abjad.Viola(),
    "keyboard": abjad.Piano(name="keyboard", short_name="kbd."),
}


STANDARD_TEMPI = (
    40,
    42,
    44,
    46,
    48,
    50,
    52,
    54,
    56,
    58,
    60,
    63,
    66,
    69,
    72,
    76,
    80,
    84,
    88,
    92,
    96,
    100,
    104,
    108,
    112,
    116,
    120,
    126,
    132,
    138,
    144,
    152,
    160,
    168,
    176,
    184,
    192,
    200,
    208,
)


# Each subtuple is composed of (TIME_SIGNATURE, COMPOSITION-STRUCTURE-OF-TS-FOR-1/8-Grid).
AVAILABLE_TIME_SIGNATURES = (
    ((2, 4), (2, 2)),
    ((4, 4), (2, 2, 2)),
    ((6, 8), (2, 3)),
    ((3, 4), (3, 2)),
    ((5, 4), (2, 5)),
    ((10, 8), (5, 2)),
)

TIME_SIGNATURES2COMPOSITION_STRUCTURES = {
    abjad.TimeSignature(ts): composition
    for ts, composition in AVAILABLE_TIME_SIGNATURES
}

METRICAL_PRIMES = (3, 4, 5)

COMPOSITION_PATH = "aml/composition"
BUILD_PATH = "aml/build"
PARTBOOKS_PATH = "aml/build/partbooks"
INTRODUCTION_PATH = "aml/build/introduction"
INTRODUCTION_PICTURES_PATH = "aml/build/introduction/pictures"

PYO_SERVER = pyo.Server(sr=44100, audio="offline", nchnls=3)
PYO_SERVER.boot()


ADD_COMPROVISATION = False

# paper format for score
FORMAT = mus.A4
