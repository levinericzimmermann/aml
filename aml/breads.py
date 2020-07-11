import functools
import operator

import quicktions as fractions

from mu.mel import ji
from mu.sco import old
from mu.rhy import indispensability
from mu.utils import tools

from aml import globals_


class Slice(object):
    def __init__(
        self,
        start: fractions.Fraction,
        stop: fractions.Fraction,
        does_slice_start_overlap_with_attack: bool,
        melody_pitch: ji.JIPitch = None,
        harmonic_pitch: ji.JIPitch = None,
        harmonic_field: dict = None,
    ) -> None:
        self.start = start
        self.stop = stop
        self.does_slice_start_overlap_with_attack = does_slice_start_overlap_with_attack
        self.melody_pitch = melody_pitch
        self.harmonic_pitch = harmonic_pitch
        self.harmonic_field = harmonic_field

    def __hash__(self) -> int:
        hasht = (self.start, self.stop, self.melody_pitch, self.harmonic_pitch)

        if self.harmonic_field:
            hasht += (tuple(sorted(self.harmonic_field.keys())),)
        else:
            hasht += (None,)

        return hash(hasht)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __repr__(self) -> str:
        repr_inner = "({}, {})".format(self.start, self.stop)
        if self.melody_pitch:
            repr_inner += ", {}".format(self.melody_pitch)

        if self.harmonic_pitch:
            repr_inner += ", {}".format(self.harmonic_pitch)

        return "Slice({})".format(repr_inner)


class Bread(object):
    def __init__(self, *slices: Slice):
        self._slices = tuple(slices)

    def index(self, slice_: Slice) -> int:
        return self._slices.index(slice_)

    def __repr__(self) -> str:
        return "Bread({})".format(self._slices)

    def __getitem__(self, idx: int) -> Slice:
        return self._slices[idx]

    def __iter__(self) -> iter:
        return iter(self._slices)

    def __len__(self) -> int:
        return len(self._slices)

    def find_responsible_slices(
        self, start: fractions.Fraction, stop: fractions.Fraction
    ) -> tuple:
        return tuple(
            slice_
            for slice_ in self
            if not (slice_.stop <= start or stop <= slice_.start)
        )

    def find_indices_of_responsible_slices(
        self, start: fractions.Fraction, stop: fractions.Fraction
    ) -> tuple:
        return tuple(
            idx
            for idx, slice_ in enumerate(self)
            if not (slice_.stop <= start or stop <= slice_.start)
        )

    def get_indices_of_slices_with_no_melodic_pitches(self) -> tuple:
        return tuple(
            idx for idx, slice_ in enumerate(self) if slice_.melody_pitch is None
        )

    def extend_harmonic_pitches(self) -> None:
        """Assign harmonic pitches to slices before melodic rests.

        The assigned harmonic pitches will be the same as their left neighbour.
        """
        candidates = tuple(
            idx - 1 for idx in self.get_indices_of_slices_with_no_melodic_pitches()
        )
        for candidate_idx in candidates:
            try:
                candidate = self[candidate_idx]
                previous_item = self[candidate_idx - 1]
            except IndexError:
                pass
            else:
                candidate.harmonic_pitch = previous_item.harmonic_pitch

    @staticmethod
    def _get_position_metricity_pairs(
        time_signature: tuple, smallest_unit: fractions.Fraction
    ) -> tuple:
        ts = fractions.Fraction(
            time_signature[0].numerator, time_signature[0].denominator
        )
        current_unit_size = ts / functools.reduce(operator.mul, time_signature[1])
        smallest_unit = min((smallest_unit, current_unit_size))
        factors = tuple(time_signature[1])
        if smallest_unit < current_unit_size:
            factors += (int(current_unit_size / smallest_unit),)

        metricities = tools.scale(
            indispensability.indispensability_for_bar(factors), 0, 1
        )
        return tuple((smallest_unit, metricity) for metricity in metricities)

    @classmethod
    def from_melody(
        cls,
        melody: old.Melody,
        bars: tuple,
        max_rest_size_to_ignore: fractions.Fraction = fractions.Fraction(1, 4),
        maximum_deviation_from_center: float = 0.5,
    ) -> "Bread":
        try:
            assert (
                maximum_deviation_from_center >= 0
                and maximum_deviation_from_center <= 1
            )
        except AssertionError:
            msg = "maximum_deviation_from_center has to be in range 0-1"
            raise ValueError(msg)

        adapted_melody = melody.tie().discard_rests(max_rest_size_to_ignore)
        smallest_unit_to_split = min(
            t.delay for t in adapted_melody if not t.pitch.is_empty
        )
        if smallest_unit_to_split.numerator == 1:
            smallest_unit = fractions.Fraction(
                1, smallest_unit_to_split.denominator * 2
            )
        else:
            smallest_unit = fractions.Fraction(1, smallest_unit_to_split.denominator)

        position_metricity_pairs_per_bar = (
            cls._get_position_metricity_pairs(
                (ts, globals_.TIME_SIGNATURES2COMPOSITION_STRUCTURES[ts]), smallest_unit
            )
            for ts in bars
        )
        positions, metricities = zip(
            *tuple(functools.reduce(operator.add, position_metricity_pairs_per_bar))
        )
        positions = tools.accumulate_from_zero(positions)[:-1]

        slices = []

        for tone in adapted_melody.convert2absolute():
            if tone.pitch.is_empty:
                mp = None
                slices.append(Slice(tone.delay, tone.duration, False, mp))
            else:
                mp = tone.pitch

                # figure out where to split the tone:

                # (1) find possible split position - candidates
                dev_range = (tone.duration - tone.delay) / 2
                center = dev_range + tone.delay
                actual_dev = dev_range * maximum_deviation_from_center
                dev0, dev1 = center - actual_dev, center + actual_dev
                available_split_positions = tuple(
                    (pos, met)
                    for pos, met in zip(positions, metricities)
                    if pos > dev0 and pos < dev1
                )

                # (2) choose the one with the highest metricity
                split_position = max(
                    available_split_positions, key=operator.itemgetter(1)
                )[0]

                # add both slices
                for start, stop, does_slice_start_overlap_with_attack in (
                    (tone.delay, split_position, True),
                    (split_position, tone.duration, False),
                ):
                    slices.append(
                        Slice(start, stop, does_slice_start_overlap_with_attack, mp)
                    )

        return cls(*slices)
