import operator

import quicktions as fractions

from mu.mel import ji
from mu.sco import old
from mu.utils import infit

from aml import complex_meters
from aml import globals_


class Area(object):
    _distribution_cycle = infit.Cycle(
        (
            (
                0,
                1,
                0,
                2,
                0,
                2,
                0,
                1,
                0,
                2,
                0,
                1,
                0,
                1,
                0,
                2,
                0,
                2,
                0,
                1,
                0,
                1,
                0,
                2,
                0,
                1,
                0,
                2,
                0,
                2,
                0,
                1,
            ),
            (
                0,
                2,
                0,
                1,
                0,
                1,
                0,
                2,
                0,
                1,
                0,
                2,
                0,
                2,
                0,
                1,
                0,
                1,
                0,
                2,
                0,
                2,
                0,
                1,
                0,
                2,
                0,
                1,
                0,
                1,
                0,
                2,
            ),
        )
    )

    def __init__(
        self,
        increment: float,
        stop: float,
        events: tuple,
        density: float,
        density_reference: fractions.Fraction,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        min_split_size: fractions.Fraction(1, 4),
    ):
        self._increment = fractions.Fraction(increment)
        self._stop = fractions.Fraction(stop)
        self._duration = self.stop - self.increment
        self._events = events
        self._absolute_events = tuple(old.Melody(events).convert2absolute())
        self._pitch = events[0].pitch

        if self.pitch.is_empty:
            self._instrument = None
            self._string_events = tuple([])
            self._sine_events = tuple([])

        else:
            self._instrument = globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[
                globals_.PITCH2INSTRUMENT[self.pitch.normalize()]
            ]

            # only split events if the complete duration of the event is bigger than one
            # quarter note.
            if self.duration > min_split_size:
                # where (start, metricity)
                rmp = spread_metrical_loop.get_rhythm_metricity_pairs_for_instrument(
                    self._instrument.name, self.increment, self.stop
                )

                assert rmp[0][0] == self.increment

                rmp = tuple((pair[0] - self.increment, pair[1]) for pair in rmp)
                rhythm_metricity_pairs = rmp

                true_density = (self.duration / density_reference) * density

                self._events2distribute = self._find_events2distribute(
                    true_density, rhythm_metricity_pairs
                )
                self._string_events, self._sine_events = self._distribute_events(
                    self._events2distribute
                )

            # for small durations, just play simultanously and synchronized
            else:
                events = ((self.increment, self.stop, 1),)
                self._string_events = events
                self._sine_events = events

    def __eq__(self, other) -> bool:
        try:
            return all(
                (
                    self.increment == other.increment,
                    self.stop == other.stop,
                    self.events == other.events,
                )
            )
        except AttributeError:
            return False

    def _find_events2distribute(
        self, density: float, rhythm_metricity_pairs: tuple
    ) -> tuple:
        n_available_rhythm_metricity_pairs = len(rhythm_metricity_pairs) - len(
            self.events
        )
        n_added_events = int(n_available_rhythm_metricity_pairs * density)
        start_positions_of_mandatory_events = tuple(
            ev.delay for ev in self.absolute_events
        )
        absolute_events_to_choose_from = tuple(
            rm
            for rm in rhythm_metricity_pairs
            if rm[0] not in start_positions_of_mandatory_events
        )
        choosen_events = sorted(
            absolute_events_to_choose_from, key=operator.itemgetter(1)
        )[:n_added_events]
        available_events = tuple((ev[0], 0) for ev in choosen_events)
        available_events += tuple(
            (start_pos, 1) for start_pos in start_positions_of_mandatory_events
        )
        available_events = sorted(available_events, key=operator.itemgetter(0))
        available_events_with_stop = []
        for event0, event1 in zip(
            available_events, available_events[1:] + [(self.duration, None)]
        ):
            start, event_type = event0
            duration = start + (event1[0] - start)
            available_events_with_stop.append(
                (fractions.Fraction(start), fractions.Fraction(duration), event_type)
            )

        return tuple(available_events_with_stop)

    @staticmethod
    def _simplify_events_within_one_instrument(events: tuple) -> tuple:
        def combine_events(events: tuple) -> tuple:
            return (events[0][0], events[-1][1], events[0][2])

        simplified_events = []
        if events:
            combineable_events = [events[0]]

            for event in events[1:]:
                is_combineable = all(
                    (event[2] == 0, event[0] == combineable_events[-1][1])
                )

                if is_combineable:
                    combineable_events.append(event)
                else:
                    simplified_events.append(combine_events(combineable_events))
                    combineable_events = [event]

            simplified_events.append(combine_events(combineable_events))

        return tuple(simplified_events)

    def _distribute_events(self, events2distribute: tuple) -> tuple:
        distribution_cycle = infit.Cycle(next(self._distribution_cycle))
        sine_events = []
        string_events = []
        for event in events2distribute:
            adapted_event = (
                event[0] + self.increment,
                event[1] + self.increment,
                event[2],
            )
            distribution = next(distribution_cycle)
            if distribution == 0:
                sine_events.append(adapted_event)
                string_events.append(adapted_event)
            elif distribution == 1:
                string_events.append(adapted_event)
            else:
                sine_events.append(adapted_event)

        string_events, sine_events = (
            self._simplify_events_within_one_instrument(string_events),
            self._simplify_events_within_one_instrument(sine_events),
        )
        return string_events, sine_events

    def __repr__(self) -> str:
        return "Area({}, {}, {})".format(self.pitch, self.duration, len(self))

    def __len__(self) -> int:
        # how many events does this area contain
        return len(self.events)

    @property
    def increment(self) -> float:
        return self._increment

    @property
    def stop(self) -> float:
        return self._stop

    @property
    def events(self) -> tuple:
        return self._events

    @property
    def absolute_events(self) -> tuple:
        return self._absolute_events

    def is_empty(self) -> bool:
        return self.pitch.is_empty

    def copy(self) -> "Area":
        return type(self)(self.events)

    @property
    def pitch(self) -> ji.JIPitch:
        return self._pitch

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def string_events(self) -> tuple:
        return self._string_events

    @property
    def non_string_events(self) -> tuple:
        non_string_events = []
        if self.string_events[0][0] != self.increment:
            non_string_events.append((self.increment, self.string_events[0][0]))

        for event0, event1 in zip(
            self.string_events, self.string_events[1:] + ((self.stop,),)
        ):
            if event0[1] != event1[0]:
                non_string_events.append((event0[1], event1[0]))

        return tuple(non_string_events)

    @property
    def sine_events(self) -> tuple:
        return self._sine_events

    @property
    def responsible_string_instrument(self) -> globals_._AdaptedInstrument:
        return self._instrument

    def is_event_overlapping_with_sine_events(self, event: tuple) -> bool:
        sta, sto, *_ = event
        for sine_event in self.sine_events:
            ssta, ssto, *_ = sine_event
            if not (sta >= ssto or ssta >= sto):
                return True

        return False


class Areas(tuple):
    def __repr__(self) -> str:
        return "Areas{}".format(tuple(self[:]))

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def from_melody(
        cls,
        melody: old.Melody,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        density_maker: infit.InfIt = infit.Gaussian(0.5, 0.2),
        density_reference: fractions.Fraction = fractions.Fraction(2, 1),
        min_split_size: fractions.Fraction = fractions.Fraction(1, 4),
    ) -> "Areas":
        areas = []
        absolute_melody = melody.convert2absolute()

        last_events = [(melody[0], absolute_melody[0])]
        for tone, absolute_tone in zip(melody[1:], absolute_melody[1:]):
            if tone.pitch == last_events[-1][0].pitch:
                last_events.append((tone, absolute_tone))
            else:
                areas.append(
                    Area(
                        last_events[0][1].delay,
                        last_events[-1][1].duration,
                        tuple(map(operator.itemgetter(0), last_events)),
                        next(density_maker),
                        density_reference,
                        spread_metrical_loop,
                        min_split_size,
                    )
                )
                last_events = [(tone, absolute_tone)]

        areas.append(
            Area(
                last_events[0][1].delay,
                last_events[-1][1].duration,
                tuple(map(operator.itemgetter(0), last_events)),
                next(density_maker),
                density_reference,
                spread_metrical_loop,
                min_split_size,
            )
        )

        return cls(areas)
