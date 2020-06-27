import functools
import numpy as np
import operator

import abjad

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


ORCHESTRATION = mus.Orchestration(
    *tuple(
        mus.MetaTrack(name, n_staves, volume, panning)
        for name, n_staves, volume, panning in (
            ("violin", 2, 1, 0.2),
            ("viola", 2, 1, 0.4),
            ("cello", 2, 1, 0.6),
            ("keyboard", 3, 1, 0.8),
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
            "dftf",
            "dqf",
            "efxf",
            "etrf",
            "estf",
            "f",
            "fxs",
            "fqs",
            "gqf",
            "gxf",
            "g",
            "atrf",
            "astf",
            "aftf",
            "bfxf",
            "btrf",
            "bf",
        ),
    )
}

SCALE_PER_INSTRUMENT = {
    instr: tuple(p.normalize() for p in _load_scale(idx))
    for idx, instr in enumerate(("violin", "viola", "cello"))
}

A_CONCERT_PITCH = 442  # a' with 442 Hz
CONCERT_PITCH = A_CONCERT_PITCH / (pow(2, 1 / 12) ** 9)


def _detect_closeness_from_pitch_x_to_pitch_y(
    intonations_per_scale_degree: tuple
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
