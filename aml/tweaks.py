"""
Collection of small functions that may help during post-processing of algorithmically
generated musical data.
"""

import functools
import operator
import logging
import quicktions as fractions

from mu.utils import tools

from mutools import mus
from mutools import lily

from aml import globals_


def remove(nth_event: int, novent_line: lily.NOventLine) -> None:
    """if following / previous event is a rest the function is concatenating the rests"""

    def assimilate(idx2assimilate: int, idx2delete: int):
        novent_line[idx2assimilate].delay += novent_line[idx2delete].delay
        novent_line[idx2assimilate].duration += novent_line[idx2delete].duration
        del novent_line[idx2delete]

    previous_event_is_rest = False
    next_event_is_rest = False

    if nth_event != 0:
        previous_event_is_rest = not novent_line[nth_event - 1].pitch

    if nth_event + 1 != len(novent_line):
        next_event_is_rest = not novent_line[nth_event + 1].pitch

    if previous_event_is_rest and next_event_is_rest:
        for _ in range(2):
            assimilate(nth_event - 1, nth_event)

    elif previous_event_is_rest:
        assimilate(nth_event - 1, nth_event)

    elif next_event_is_rest:
        assimilate(nth_event + 1, nth_event)

    else:
        novent_line[nth_event].pitch = []


def prolong(
    nth_event: int, value: fractions.Fraction, novent_line: lily.NOventLine
) -> None:
    tests = (
        not novent_line[nth_event + 1].pitch,
        novent_line[nth_event + 1].delay >= value,
    )

    try:
        assert all(tests)

    except AssertionError:
        msg = "Can't prolong duration of event because following event isn't a rest or "
        msg += "isn't long enough."
        raise ValueError(msg)

    novent_line[nth_event].delay += value
    novent_line[nth_event].duration += value

    if novent_line[nth_event + 1].delay == value:
        del novent_line[nth_event + 1]

    else:
        novent_line[nth_event + 1].delay -= value
        novent_line[nth_event + 1].duration -= value


def shorten(
    nth_event: int, value: fractions.Fraction, novent_line: lily.NOventLine
) -> None:
    try:
        assert novent_line[nth_event].delay > value

    except AssertionError:
        msg = "Can't shorten event '{}' by value '{}'. Event is too short!".format(
            novent_line[nth_event], value
        )
        raise ValueError(msg)

    novent_line[nth_event].delay -= value
    novent_line[nth_event].duration -= value

    if nth_event + 1 != len(novent_line):
        if not novent_line[nth_event + 1].pitch:
            novent_line[nth_event + 1].delay += value
            novent_line[nth_event + 1].duration += value
            return

    novent_line.insert(
        nth_event + 1, lily.NOventLine(pitch=[], delay=value, duration=value)
    )


def split(
    nth_event: int,
    novent_line: lily.NOventLine,
    *duration_of_splitted_event,
    change_novent_line: bool = True
) -> None:
    duration = sum(duration_of_splitted_event)

    try:
        assert duration == novent_line[nth_event].delay

    except AssertionError:
        msg = (
            "Summed duration of each splitted event has to be as long as the duration "
        )
        msg += "of the event that shall be splitted."
        raise ValueError(msg)

    event2split = novent_line[nth_event].copy()

    if change_novent_line:
        del novent_line[nth_event]

    else:
        splitted_novents = []

    for duration in reversed(duration_of_splitted_event):
        splitted_novent = event2split.copy()
        splitted_novent.delay = duration
        splitted_novent.duration = duration
        if change_novent_line:
            novent_line.insert(nth_event, splitted_novent)
        else:
            splitted_novents.insert(0, splitted_novent)

    if not change_novent_line:
        return tuple(splitted_novents)


def split_by_structure(
    nth_event: int,
    split_to_n_items: int,
    novent_line: lily.NOventLine,
    verse_maker: mus.SegmentMaker,
    change_novent_line: bool = True,
) -> None:
    assert split_to_n_items > 0

    if novent_line[nth_event].pitch:
        absolute_novent_line = tools.accumulate_from_zero(
            tuple(novent_line.__delay._LinkedList__iterable)
        )
        start, stop = (
            absolute_novent_line[nth_event],
            absolute_novent_line[nth_event + 1],
        )

        sml = verse_maker.transcription.spread_metrical_loop
        instruments = tuple(
            globals_.PITCH2INSTRUMENT[pitch.normalize()]
            for pitch in novent_line[nth_event].pitch
        )

        available_positions = tuple(
            set(
                functools.reduce(
                    operator.add,
                    (
                        sml.get_rhythm_metricity_pairs_for_instrument(
                            instrument, start, stop
                        )
                        for instrument in instruments
                    ),
                )
            )
        )

        if len(available_positions) < split_to_n_items:
            msg = "It can only be split to {} items because more positions ".format(
                len(available_positions)
            )
            msg += "aren't available."
            logging.warn(msg)

        if len(available_positions) > 1:
            start_positions_of_splitted_attack = [start]
            for position_and_metricity in tuple(
                filter(
                    lambda pos: pos[0] != start and pos[0] != stop,
                    sorted(
                        available_positions, key=operator.itemgetter(1), reverse=True
                    ),
                )
            )[: split_to_n_items - 1]:
                position, _ = position_and_metricity
                start_positions_of_splitted_attack.append(position)

            sorted_start_positions = sorted(start_positions_of_splitted_attack)
            durations = tuple(
                b - a
                for a, b in zip(
                    sorted_start_positions, sorted_start_positions[1:] + [stop]
                )
            )

            return split(
                nth_event,
                novent_line,
                *durations,
                change_novent_line=change_novent_line
            )

    else:
        msg = (
            "Can't split rests by pauses! Function can only split events that contain "
        )
        msg += "pitch information."
        logging.warn(msg)
