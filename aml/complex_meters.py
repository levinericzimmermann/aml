import functools
import itertools
import operator
import quicktions as fractions

import abjad

import crosstrainer

from mu.mel import mel
from mu.sco import old
from mu.rhy import indispensability
from mu.utils import tools

from aml import globals_


class Bar(abjad.TimeSignature):
    _smallest_expected_unit = fractions.Fraction(1, 32)
    _available_time_signatures = tuple(zip(*globals_.AVAILABLE_TIME_SIGNATURES))[0]

    def __init__(self, ts: tuple):
        assert ts in self._available_time_signatures
        super().__init__(ts)

        self._metricity_per_beat = self._calculate_metricity_per_beat()
        self._sorted_metricity_per_beat = tuple(
            sorted(self._metricity_per_beat, reverse=True)
        )
        self._sorted_beat_metricity_pairs = tuple(
            (self._metricity_per_beat.index(metricity), metricity)
            for metricity in self._sorted_metricity_per_beat
        )
        self._n_beats = len(self._metricity_per_beat)

    def _calculate_metricity_per_beat(self) -> tuple:
        primes = list(
            globals_.TIME_SIGNATURES2COMPOSITION_STRUCTURES[
                abjad.TimeSignature((self.numerator, self.denominator))
            ]
        )
        duration = self.duration

        while (
            duration / functools.reduce(operator.mul, primes)
            > self._smallest_expected_unit
        ):
            primes.append(2)

        return tools.scale(
            indispensability.indispensability_for_bar(tuple(primes)), 0, 1
        )

    def __hash__(self) -> int:
        return hash((self.numerator, self.denominator))

    def __eq__(self, other):
        try:
            return self.time_signature == other.time_signature
        except AttributeError:
            return False

    def __repr__(self) -> str:
        return "Bar({}, {})".format(self.numerator, self.denominator)

    def get_pulse_rhythm_and_metricity_per_beat(self, n_attacks: int) -> tuple:
        assert n_attacks <= self._n_beats
        beat_metricity_pairs = sorted(
            self._sorted_beat_metricity_pairs[:n_attacks], key=operator.itemgetter(0)
        )
        beats = tuple(
            int(b[0] - a[0]) * self._smallest_expected_unit
            for a, b in zip(
                beat_metricity_pairs, beat_metricity_pairs[1:] + [(self._n_beats,)]
            )
        )
        metricities = tuple(map(operator.itemgetter(1), beat_metricity_pairs))
        return beats, metricities


class Point(object):
    def __init__(
        self,
        metrical_prime: int,
        nth: int,
        nth_loop: int,
        rhythm_and_metricity_per_prime: dict,
        loop_size: fractions.Fraction,
    ):
        self._nth = nth
        self._nth_loop = nth_loop
        self._metrical_prime = metrical_prime
        self._rhythm_and_metricity_per_prime = rhythm_and_metricity_per_prime
        self._loop_size = loop_size

    def __repr__(self) -> str:
        return "Point({}, {}, {})".format(self.nth, self.nth_loop, self.metrical_prime)

    @property
    def nth_loop(self) -> int:
        return self._nth_loop

    @property
    def nth(self) -> int:
        return self._nth

    @property
    def metrical_prime(self) -> int:
        return self._metrical_prime

    @property
    def position(self) -> float:
        return self.relative_position + (self._loop_size * self._nth_loop)

    @property
    def relative_position(self) -> float:
        return self._rhythm_and_metricity_per_prime[self._metrical_prime][0][self._nth]

    @property
    def metricity(self) -> float:
        return self._rhythm_and_metricity_per_prime[self._metrical_prime][1][self._nth]

    def find_next_position(
        self, next_metrical_prime: int, expected_difference: fractions.Fraction
    ):
        expected_position = self.relative_position + expected_difference
        next_metrical_prime_rhythms = self._rhythm_and_metricity_per_prime[
            next_metrical_prime
        ][0]
        test_area = next_metrical_prime_rhythms + (self._loop_size,)
        n_loops_added = 0
        closest_index = tools.find_closest_index(expected_position, test_area)

        while test_area[closest_index] == self._loop_size:
            expected_position -= self._loop_size
            closest_index = tools.find_closest_index(expected_position, test_area)
            n_loops_added += 1

        deviation = expected_position - test_area[closest_index]
        if deviation < 0 and closest_index != 0:
            candidates = (closest_index, closest_index - 1)

        elif deviation > 0 and test_area[closest_index + 1] != self._loop_size:
            candidates = (closest_index, closest_index + 1)

        else:
            candidates = None

        if candidates:
            closest_index = max(
                (
                    (
                        idx,
                        self._rhythm_and_metricity_per_prime[next_metrical_prime][1][
                            idx
                        ],
                    )
                    for idx in candidates
                ),
                key=operator.itemgetter(1),
            )[0]

        return type(self)(
            next_metrical_prime,
            closest_index,
            self._nth_loop + n_loops_added,
            self._rhythm_and_metricity_per_prime,
            self._loop_size,
        )


class SpreadMetricalLoop(object):
    def __init__(
        self,
        n_repetitions: int,
        # how many beats one loop containts
        loop_duration: fractions.Fraction,
        # how many bars one loop containts
        loop_size: int,
        bars: tuple,
        rhythm_and_metricity_per_prime: dict,
        instrument_prime_mapping: dict,
    ):
        self._n_repetitions = n_repetitions
        self._basic_bars = bars
        self._bars = tuple(tuple(abjad.TimeSignature(b) for b in bars) * n_repetitions)
        self._loop_duration = loop_duration
        self._duration = loop_duration * n_repetitions
        self._loop_size = loop_size
        self._instrument_prime_mapping = instrument_prime_mapping
        self._absolute_rhythm_and_metricity_per_prime = {
            prime: (
                (
                    # absolute rhythms
                    tools.accumulate_from_zero(
                        rhythm_and_metricity_per_prime[prime][0] * n_repetitions
                    )[:-1],
                    # metricities, rescaled to range 0 - 1
                    tuple(
                        tools.scale(rhythm_and_metricity_per_prime[prime][1], 0, 1)
                        * n_repetitions
                    ),
                )
            )
            for prime in rhythm_and_metricity_per_prime
        }
        absolute_rhythm_and_metricities = functools.reduce(
            operator.add,
            (
                tuple(zip(*self._absolute_rhythm_and_metricity_per_prime[prime]))
                for prime in self._absolute_rhythm_and_metricity_per_prime
            ),
        )

        absolute_rhythm_and_metricities_dict = {}
        for position, metricity in absolute_rhythm_and_metricities:
            is_addable = True
            if position in absolute_rhythm_and_metricities_dict:
                if metricity < absolute_rhythm_and_metricities_dict[position]:
                    is_addable = False

            if is_addable:
                absolute_rhythm_and_metricities_dict.update({position: metricity})

        self._absolute_rhythm_and_metricities = tuple(
            sorted(
                (
                    (position, absolute_rhythm_and_metricities_dict[position])
                    for position in absolute_rhythm_and_metricities_dict
                ),
                key=operator.itemgetter(0),
            )
        )

        self._absolute_rhythm = tuple(
            map(operator.itemgetter(0), self._absolute_rhythm_and_metricities)
        )
        self._metricities = tuple(
            map(operator.itemgetter(1), self._absolute_rhythm_and_metricities)
        )

    def __repr__(self) -> str:
        return "SpreadMetricalLoop({})".format(self._basic_bars)

    @property
    def duration(self) -> fractions.Fraction:
        return self._duration

    @property
    def instrument_prime_mapping(self) -> dict:
        return self._instrument_prime_mapping

    @property
    def prime_instrument_mapping(self) -> dict:
        return {
            prime: instrument
            for instrument, prime in self.instrument_prime_mapping.items()
        }

    @property
    def loop_duration(self) -> int:
        return self._loop_duration

    @property
    def loop_size(self) -> int:
        return self._loop_size

    @property
    def bars(self) -> tuple:
        return self._bars

    @property
    def n_repetitions(self) -> int:
        return self._n_repetitions

    def get_primes_of_absolute_rhythm(self, absolute_rhythm: float) -> tuple:
        primes = []
        for prime in self._absolute_rhythm_and_metricity_per_prime:
            if (
                absolute_rhythm
                in self._absolute_rhythm_and_metricity_per_prime[prime][0]
            ):
                primes.append(prime)

        if primes:
            return tuple(primes)

        raise KeyError("No prime contains absolute rhythm {}.".format(absolute_rhythm))

    def get_metricities_for_prime(self, prime: int) -> tuple:
        return self._absolute_rhythm_and_metricity_per_prime[prime][1]

    def get_rhythms_for_prime(self, prime: int) -> tuple:
        return self._absolute_rhythm_and_metricity_per_prime[prime][0]

    def get_all_rhythms(self) -> tuple:
        return self._absolute_rhythm

    def get_all_metricities(self) -> tuple:
        return self._metricities

    def get_all_rhythm_metricitiy_pairs(self, start=None, stop=None) -> tuple:
        absolute_rhythm_and_metricities = self._absolute_rhythm_and_metricities
        start_idx = 0

        if start:
            start_idx = tools.find_closest_index(
                start, absolute_rhythm_and_metricities, key=operator.itemgetter(0)
            )
            if absolute_rhythm_and_metricities[start_idx][0] < start:
                start_idx += 1

        if stop:
            stop_idx = tools.find_closest_index(
                stop, absolute_rhythm_and_metricities, key=operator.itemgetter(0)
            )
            if absolute_rhythm_and_metricities[stop_idx][0] < stop:
                stop_idx += 1

        else:
            stop_idx = len(absolute_rhythm_and_metricities)

        return self._absolute_rhythm_and_metricities[start_idx:stop_idx]

    def get_rhythms_for_instrument(self, instrument: str) -> tuple:
        return self.get_rhythms_for_prime(self.instrument_prime_mapping[instrument])

    def get_metricities_for_instrument(self, instrument: str) -> tuple:
        return self.get_metricities_for_prime(self.instrument_prime_mapping[instrument])


class MetricalLoop(object):
    def __init__(self, *bars: Bar) -> tuple:
        self._primes = globals_.METRICAL_PRIMES
        self._size = functools.reduce(operator.mul, self._primes)
        self._n_attacks_per_bar = self._find_n_attacks_per_bar(
            self._primes, bars, self._size
        )
        self._bars = tuple(bars)
        self._duration = sum(b.duration for b in self.bars)
        self._pulse_rhythm_and_metricity_per_beat = (
            self._get_pulse_rhythm_and_metricity_per_beat()
        )
        self._rhythm_and_metricity_per_prime = (
            self._get_rhythm_and_metricity_per_prime()
        )
        self._absolute_rhythm_and_metricity_per_prime = (
            self._get_absolute_rhythm_and_metricity_per_prime()
        )

    def __repr__(self) -> str:
        return "MetricalLoop({})".format(self.bars)

    @staticmethod
    def _find_n_attacks_per_bar(
        primes: tuple, bars: tuple, n_attacks2distribute: int
    ) -> tuple:
        summed_bars = sum(b.duration for b in bars)
        smallest_denominator = min(b.duration.denominator for b in bars)
        scd = n_attacks2distribute / (summed_bars * smallest_denominator)

        try:
            assert int(scd) == scd
        except AssertionError:
            msg = "Primes bar connection doesn't work. "
            msg += "Smallest common denominator is {}".format(scd)
            raise ValueError(msg)

        return tuple(int(scd * smallest_denominator * b.duration) for b in bars)

    @property
    def n_attacks_per_bar(self) -> tuple:
        return self._n_attacks_per_bar

    @property
    def primes(self) -> tuple:
        return self._primes

    @property
    def bars(self) -> tuple:
        return self._bars

    @property
    def duration(self) -> abjad.Duration:
        return self._duration

    def __eq__(self, other):
        try:
            return self.bars == other.bars
        except AttributeError:
            return False

    def _get_pulse_rhythm_and_metricity_per_beat(self) -> tuple:
        pr_and_metr_per_bar = tuple(
            bar.get_pulse_rhythm_and_metricity_per_beat(n_attacks)
            for bar, n_attacks in zip(self.bars, self.n_attacks_per_bar)
        )
        return tuple(
            functools.reduce(operator.add, d) for d in zip(*pr_and_metr_per_bar)
        )

    def _get_absolute_rhythm_and_metricity_per_prime(self) -> tuple:
        return {
            prime: (
                tools.accumulate_from_zero(
                    self._rhythm_and_metricity_per_prime[prime][0]
                )[:-1],
                self._rhythm_and_metricity_per_prime[prime][1],
            )
            for prime in self._rhythm_and_metricity_per_prime
        }

    def _get_rhythm_and_metricity_per_prime(self) -> dict:
        data_per_prime = {}

        for prime in self.primes:
            resulting_rhythm = tools.accumulate_from_zero(
                self._pulse_rhythm_and_metricity_per_beat[0]
            )[::prime]
            duration = sum(self._pulse_rhythm_and_metricity_per_beat[0])
            if resulting_rhythm[-1] != duration:
                resulting_rhythm.append(duration)
            resulting_rhythm = tuple(
                fractions.Fraction(b - a)
                for a, b in zip(resulting_rhythm, resulting_rhythm[1:])
            )
            metricities = self._pulse_rhythm_and_metricity_per_beat[1][::prime]
            data_per_prime.update({prime: (resulting_rhythm, metricities)})

        return data_per_prime

    def transform_melody(
        self,
        melody: old.Melody,
        mapping: dict = {
            instr: prime
            for prime, instr in zip(
                globals_.METRICAL_PRIMES, ("violin", "viola", "cello")
            )
        },
    ) -> tuple:
        prime_number_per_event = []
        for tone in melody:
            if tone.pitch.is_empty:
                if prime_number_per_event:
                    prime_number_per_event.append(prime_number_per_event[-1])

                else:
                    prime_number_per_event.append(None)

            else:
                prime_number_per_event.append(
                    mapping[globals_.PITCH2INSTRUMENT[tone.pitch.normalize()]]
                )

        if prime_number_per_event[0] is None:
            prime_number_per_event[0] = int(prime_number_per_event[1])

        # as high metricity as possible / as low deviation as possible
        hof = crosstrainer.MultiDimensionalRating(size=2, fitness=[1, -1])

        n_possible_offsets = len(
            self._rhythm_and_metricity_per_prime[prime_number_per_event[0]][0]
        )
        for n_offsets in range(n_possible_offsets):
            if n_offsets > 0:
                adapted_melody = melody.copy()
                offset_duration = sum(
                    self._rhythm_and_metricity_per_prime[prime_number_per_event[0]][0][
                        :n_offsets
                    ]
                )
                adapted_melody.insert(
                    0, old.Tone(mel.TheEmptyPitch, delay=offset_duration)
                )
                adapted_prime_number_per_event = (prime_number_per_event[0],) + tuple(
                    prime_number_per_event
                )

            else:
                adapted_melody = melody.copy()
                adapted_prime_number_per_event = tuple(prime_number_per_event)

            expected_distances = tuple(
                fractions.Fraction(d) for d in adapted_melody.delay
            )

            positions = [
                Point(
                    adapted_prime_number_per_event[0],
                    0,
                    0,
                    self._absolute_rhythm_and_metricity_per_prime,
                    self.duration,
                )
            ]
            for expected_distance, prime_number in zip(
                expected_distances,
                adapted_prime_number_per_event[1:]
                + (adapted_prime_number_per_event[-1],),
            ):
                positions.append(
                    positions[-1].find_next_position(prime_number, expected_distance)
                )

            absolute_rhythm = tuple(p.position for p in positions)
            complete_duration = (positions[-1].nth_loop + 1) * self.duration

            if absolute_rhythm[-1] != complete_duration:
                absolute_rhythm += ((positions[-1].nth_loop + 1) * self.duration,)
                adapted_melody.append(old.Tone(mel.TheEmptyPitch, delay=1))

            relative_rhythm = tuple(
                b - a for a, b in zip(absolute_rhythm, absolute_rhythm[1:])
            )
            new_melody = old.Melody(
                [
                    old.Tone(pitch=t.pitch, volume=t.volume, delay=r, duration=r)
                    for t, r in zip(adapted_melody, relative_rhythm)
                ]
            )

            summed_metricity = sum(p.metricity for p in positions[:-1]) / len(positions)
            summed_deviation = sum(
                abs(exp - real)
                for exp, real in zip(expected_distances, relative_rhythm)
            )
            hof.append(
                (new_melody, positions[-1].nth_loop + 1),
                summed_metricity,
                summed_deviation,
            )

        best = hof.convert2list()[-1]
        return (best[0][0], lambda: self.spread(best[0][-1], mapping)), best[1]

    def spread(
        self, n_repetitions: int, instrument_prime_mapping: dict
    ) -> SpreadMetricalLoop:
        return SpreadMetricalLoop(
            n_repetitions,
            self.duration,
            len(self.bars),
            self.bars,
            self._rhythm_and_metricity_per_prime,
            instrument_prime_mapping,
        )


class ComplexMeterTranscriber(object):
    _available_metrical_loops = functools.reduce(
        operator.add,
        tuple(
            tuple(
                MetricalLoop(*permuted_bars)
                for permuted_bars in set(itertools.permutations(bars))
            )
            for bars in (
                (Bar((5, 4)), Bar((3, 4)), Bar((4, 4))),
                (Bar((5, 4)), Bar((6, 8)), Bar((4, 4))),
                (Bar((3, 4)), Bar((3, 4)), Bar((4, 4))),
                (Bar((6, 8)), Bar((3, 4)), Bar((4, 4))),
                (Bar((6, 8)), Bar((6, 8)), Bar((4, 4))),
                (Bar((5, 4)), Bar((5, 4))),
                (Bar((4, 4)), Bar((3, 4)), Bar((3, 4)), Bar((2, 4))),
                (Bar((2, 4)), Bar((6, 8)), Bar((4, 4)), Bar((3, 4))),
                (Bar((2, 4)), Bar((6, 8)), Bar((4, 4)), Bar((6, 8))),
                (Bar((3, 4)), Bar((2, 4)), Bar((3, 4)), Bar((2, 4))),
                (Bar((6, 8)), Bar((2, 4)), Bar((3, 4)), Bar((2, 4))),
            )
        ),
    )

    def __call__(self, melody: old.Melody) -> tuple:
        """Return (Melody, MetricalLoop) - pair."""
        possible_mappings = tuple(
            {"violin": p[0], "viola": p[1], "cello": p[2]}
            for p in itertools.permutations(globals_.METRICAL_PRIMES)
        )

        melody = old.Melody(melody)

        hof = crosstrainer.MultiDimensionalRating(fitness=[1, -1])

        c = 0
        for metrical_loop in self._available_metrical_loops:
            for mapping in possible_mappings:
                transformation = metrical_loop.transform_melody(melody, mapping)
                relevant_data, fitness = transformation
                hof.append(relevant_data, *fitness)

            c += 1

        best = hof.convert2list()[-1]
        melody, spread_metrical_loop = best[0]

        # it's only a lambda function before for preventing to generate unused objects
        spread_metrical_loop = spread_metrical_loop()

        return melody, spread_metrical_loop.bars, spread_metrical_loop
