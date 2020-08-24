"""
Collection of small functions that may help during post-processing of algorithmically
generated musical data.
"""

import functools
import logging
import operator
import quicktions as fractions

import abjad

from mu.mel import ji

from mu.sco import old

from mu.utils import interpolations
from mu.utils import tools

from mutools import attachments
from mutools import lily
from mutools import mus

from aml import globals_

from aml.trackmaker import keyboard


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


def postpone(
    nth_event: int, value: fractions.Fraction, novent_line: lily.NOventLine
) -> None:
    try:
        assert novent_line[nth_event].delay > value

    except AssertionError:
        msg = "Can't postpone event with value {} ".format(value)
        msg += "because the event isn't long enough."
        raise ValueError(msg)

    novent_line[nth_event].delay -= value
    novent_line[nth_event].duration -= value

    if nth_event == 0 or novent_line[nth_event - 1].pitch:
        novent_line.insert(
            nth_event, lily.NOvent(pitch=[], delay=value, duration=value)
        )

    else:
        novent_line[nth_event - 1].delay += value
        novent_line[nth_event - 1].duration += value


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
        nth_event + 1, lily.NOvent(pitch=[], delay=value, duration=value)
    )


def swap_duration(
    donor: int,
    receiver: int,
    swaped_size: fractions.Fraction,
    novent_line: lily.NOventLine,
) -> None:
    assert novent_line[donor].delay >= swaped_size
    novent_line[receiver].delay += swaped_size
    novent_line[receiver].duration += swaped_size

    if novent_line[donor].delay == swaped_size:
        del novent_line[donor]
    else:
        novent_line[donor].delay -= swaped_size
        novent_line[donor].duration -= swaped_size


def eat(predator: int, victim: int, novent_line: lily.NOventLine) -> None:
    swap_duration(victim, predator, novent_line[victim].duration, novent_line)


def swap_pitch(idx0: int, idx1: int, novent_line: lily.NOventLine,) -> None:
    novent_line[idx0].pitch, novent_line[idx1].pitch = (
        novent_line[idx1].pitch,
        novent_line[idx0].pitch,
    )


def swap_identity(
    idx0: int, idx1: int, novent_line: lily.NOventLine, swap_duration: bool = False
) -> None:
    """swaps everything"""

    novent_line[idx0], novent_line[idx1] = (
        novent_line[idx1],
        novent_line[idx0],
    )
    novent_line[idx0].delay, novent_line[idx1].delay = (
        novent_line[idx1].delay,
        novent_line[idx0].delay,
    )
    novent_line[idx0].duration, novent_line[idx1].duration = (
        novent_line[idx1].duration,
        novent_line[idx0].duration,
    )


def rest(idx: int, novent_line: lily.NOventLine) -> None:
    previous_is_rest = False

    if idx != 0:
        previous_is_rest = not novent_line[idx - 1].pitch

    try:
        following_is_rest = not novent_line[idx + 1].pitch
    except KeyError:
        following_is_rest = False

    if previous_is_rest and following_is_rest:
        added_duration = novent_line[idx].duration + novent_line[idx + 1].duration
        novent_line[idx - 1].delay += added_duration
        novent_line[idx - 1].duration += added_duration
        for _ in range(2):
            del novent_line[idx]

    elif previous_is_rest:
        added_duration = novent_line[idx].duration
        novent_line[idx - 1].delay += added_duration
        novent_line[idx - 1].duration += added_duration
        del novent_line[idx]

    elif following_is_rest:
        added_duration = novent_line[idx].duration
        novent_line[idx + 1].delay += added_duration
        novent_line[idx + 1].duration += added_duration
        del novent_line[idx]

    else:
        empty_event = lily.NOvent(
            pitch=[], delay=fractions.Fraction(novent_line[idx].delay)
        )
        novent_line[idx] = empty_event


def rest_many(indices: tuple, novent_line: lily.NOventLine) -> None:
    for idx in sorted(indices, reverse=True):
        rest(idx, novent_line)


def split(
    nth_event: int,
    novent_line: lily.NOventLine,
    *duration_of_splitted_event,
    change_novent_line: bool = True,
    set_n_novents2rest: int = 0,
) -> None:
    n_splits = len(duration_of_splitted_event)
    if n_splits < set_n_novents2rest:
        set_n_novents2rest = n_splits

    is_active_per_novent = tuple(
        not bool(it) for it in tools.euclid(set_n_novents2rest, n_splits)
    )

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

    for duration, is_active in zip(
        reversed(duration_of_splitted_event), is_active_per_novent
    ):
        splitted_novent = event2split.copy()
        splitted_novent.delay = duration
        splitted_novent.duration = duration

        if change_novent_line:
            novent_line.insert(nth_event, splitted_novent)
        else:
            if not is_active:
                splitted_novent = lily.NOvent(
                    pitch=[], delay=duration, duration=duration
                )
            splitted_novents.insert(0, splitted_novent)

    if not change_novent_line:
        return tuple(splitted_novents)

    else:
        for idx, is_active in enumerate(is_active_per_novent):
            if not is_active:
                rest(idx + nth_event, novent_line)


def copy_pitch(origin: int, goal: int, novent_line: lily.NOventLine) -> None:
    novent_line[goal].pitch = [p.copy() for p in novent_line[origin].pitch]


def split_by_structure(
    nth_event: int,
    split_to_n_items: int,
    novent_line: lily.NOventLine,
    verse_maker: mus.SegmentMaker,
    change_novent_line: bool = True,
    set_n_novents2rest: int = 0,
    adapt_by_changed_structure: bool = False,
) -> None:
    assert split_to_n_items > 0

    if novent_line[nth_event].pitch:
        novent_line.delay
        absolute_novent_line = tools.accumulate_from_zero(
            tuple(ev.delay for ev in novent_line)
        )
        start, stop = (
            fractions.Fraction(absolute_novent_line[nth_event]),
            fractions.Fraction(absolute_novent_line[nth_event + 1]),
        )

        if adapt_by_changed_structure:
            bar_idx = verse_maker.violin.get_responsible_bar_index(start)
            time_difference = verse_maker.time_distance_to_original_structure_per_bar[
                bar_idx
            ]
            start += time_difference
            stop += time_difference

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
                change_novent_line=change_novent_line,
                set_n_novents2rest=set_n_novents2rest,
            )

    else:
        msg = (
            "Can't split rests by pauses! Function can only split events that contain "
        )
        msg += "pitch information."
        logging.warn(msg)

    if not change_novent_line:
        return [novent_line[nth_event].copy()]


def add_glissando(
    nth_event: int,
    scale_degrees: tuple,
    novent_line: lily.NOventLine,
    durations: tuple = tuple([]),
    verse_maker: mus.SegmentMaker = None,
    adapt_by_changed_structure: bool = False,
):
    n_scale_degrees = len(scale_degrees)

    assert verse_maker or durations or n_scale_degrees in (1, 2)

    if not durations:
        if n_scale_degrees == 2:
            durations = (novent_line[nth_event].duration,)
        elif n_scale_degrees > 2:
            durations = tuple(
                fractions.Fraction(nv.delay)
                for nv in split_by_structure(
                    nth_event,
                    n_scale_degrees - 1,
                    novent_line,
                    verse_maker=verse_maker,
                    change_novent_line=False,
                    adapt_by_changed_structure=adapt_by_changed_structure,
                )
            )

    assert len(durations) == len(scale_degrees) - 1

    novent = novent_line[nth_event].copy()
    normalized_pitch = novent.pitch[0].normalize()

    instrument = globals_.PITCH2INSTRUMENT[normalized_pitch]
    octave = novent.pitch[0].octave
    pitch_zone = tuple(
        p.register(octave)
        for p in sorted(
            tuple(p.copy() for p in globals_.SCALE_PER_INSTRUMENT[instrument])
        )
    )
    pitch_zone = functools.reduce(
        operator.add,
        (tuple(p + ji.JIPitch([n - 1]) for p in pitch_zone) for n in range(3)),
    )

    pitch_null_idx = pitch_zone.index(novent.pitch[0])

    durations += (0,)

    interpolation_line = []
    for relative_pitch_class, duration in zip(scale_degrees, durations):
        pc = relative_pitch_class % 7
        octave = relative_pitch_class // 7
        pitch = pitch_zone[pc + pitch_null_idx] + ji.JIPitch([octave]) - novent.pitch[0]
        interpolation_line.append(old.PitchInterpolation(duration, pitch))

    novent_line[nth_event].glissando = old.GlissandoLine(
        interpolations.InterpolationLine(interpolation_line)
    )


def change_octave(
    nth_event: int,
    n_octaves: int,
    novent_line: lily.NOventLine,
    change_main_pitches: bool = True,
    change_acciaccatura_pitches: bool = True,
) -> None:
    if change_main_pitches:
        novent_line[nth_event].pitch = [
            p + ji.JIPitch([n_octaves]) for p in novent_line[nth_event].pitch
        ]

    if novent_line[nth_event].acciaccatura and change_acciaccatura_pitches:
        novent_line[nth_event].acciaccatura.mu_pitches = tuple(
            p + ji.JIPitch([n_octaves])
            for p in novent_line[nth_event].acciaccatura.mu_pitches
        )
        previous_abjad_note = novent_line[nth_event].acciaccatura.abjad
        novent_line[nth_event].acciaccatura.abjad = abjad.Note(
            abjad.NamedPitch(
                name=previous_abjad_note.written_pitch.pitch_class.name,
                octave=previous_abjad_note.written_pitch.octave.number + n_octaves,
            ),
            abjad.Duration(previous_abjad_note.written_duration),
        )


def set_acciaccatura_pitch(
    nth_event: int, pitch: ji.JIPitch, novent_line: lily.NOventLine,
) -> None:
    novent_line[nth_event].acciaccatura.abjad = abjad.Note(
        lily.convert2abjad_pitch(pitch, globals_.RATIO2PITCHCLASS),
        abjad.Duration(1, 8),
    )
    novent_line[nth_event].acciaccatura.mu_pitches = [pitch]


def _get_artifical_harmonic_pitches(pitch: ji.JIPitch) -> tuple:
    ground_pitch = lily.convert2abjad_pitch(pitch, globals_.RATIO2PITCHCLASS)
    (
        harmonic_pitch_class,
        harmonic_octave_difference,
    ) = globals_.RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE[
        pitch.register(0)
    ]
    harmonic_pitch_octave = ground_pitch.octave.number + harmonic_octave_difference
    harmonic_pitch = abjad.NamedPitch(
        name=harmonic_pitch_class, octave=harmonic_pitch_octave
    )
    return abjad.PitchSegment(sorted([ground_pitch, harmonic_pitch]))


def add_artifical_harmonic(
    nth_event: int, pitch: ji.JIPitch, novent_line: lily.NOventLine
) -> None:
    novent_line[nth_event].artifical_harmonic = attachments.ArtificalHarmonicAddedPitch(
        _get_artifical_harmonic_pitches(pitch)
    )


def add_acciaccatura(
    nth_event: int,
    pitch: ji.JIPitch,
    novent_line: lily.NOventLine,
    add_glissando: bool = False,
    use_artifical_harmonic: bool = False,
) -> None:
    if use_artifical_harmonic:
        abjad_note = abjad.Chord(
            _get_artifical_harmonic_pitches(pitch), abjad.Duration(1, 8),
        )
        abjad.tweak(abjad_note.note_heads[1]).style = "harmonic"
        pitch = pitch + ji.r(4, 1)

    else:
        abjad_note = abjad.Note(
            lily.convert2abjad_pitch(pitch, globals_.RATIO2PITCHCLASS),
            abjad.Duration(1, 8),
        )
    novent_line[nth_event].acciaccatura = attachments.Acciaccatura(
        [pitch], abjad_note, add_glissando
    )


def make_solo_gong(nth_event: int, novent_line: lily.NOventLine) -> None:
    novent_line[nth_event].arpeggio = None
    novent_line[nth_event].ottava = attachments.Ottava(-1)
    novent_line[nth_event].pitch = list(sorted(novent_line[nth_event].pitch)[:1])
    novent_line[nth_event].articulation_once = None


def add_gong(
    nth_event: int,
    novent_line: lily.NOventLine,
    pitch: ji.JIPitch = None,
    pedal: bool = True,
) -> None:
    if pitch is None:
        pitches = novent_line[nth_event].pitch
    else:
        pitches = [pitch]

    novent_line[nth_event].pitch = [
        p.register(keyboard.SYMBOLIC_GONG_OCTAVE) for p in pitches
    ]
    novent_line[nth_event].pedal = attachments.Pedal(pedal)
    novent_line[nth_event].ottava = attachments.Ottava(-1)


def add_kenong(
    nth_event: int, novent_line: lily.NOventLine, pitch: ji.JIPitch = None
) -> None:
    add_gong(nth_event, novent_line, pitch=pitch, pedal=False)


def crop(
    nth_event: int,
    novent_line: lily.NOventLine,
    *duration: fractions.Fraction,
    position=True,
) -> None:
    summed_duration = sum(duration)
    ev_duration = novent_line[nth_event].duration
    try:
        assert summed_duration <= ev_duration
    except AssertionError:
        msg = "Can't crop away '{}' from event '{}'.".format(
            summed_duration, novent_line[nth_event]
        )
        raise ValueError(msg)

    difference = ev_duration - summed_duration
    if difference > 0:
        duration += (difference,)

    if not position:
        duration = tuple(reversed(duration))

    split(nth_event, novent_line, *duration)


def detach_hauptstimme(novent_line: lily.NOventLine) -> None:
    for ev in novent_line:
        ev.hauptstimme = None


def detach_optional_events(novent_line: lily.NOventLine) -> None:
    for ev in novent_line:
        ev.optional = None
        ev.optional_some_pitches = None
        ev.choose = None


def set_pizz(nth_event: int, novent_line: lily.NOventLine) -> None:
    novent_line[nth_event].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    novent_line[nth_event].volume = 1.3


def set_arco(nth_event: int, novent_line: lily.NOventLine) -> None:
    novent_line[nth_event].string_contact_point = attachments.StringContactPoint("arco")
    novent_line[nth_event].volume = 0.486


def scpm(position: str) -> abjad.Markup:
    return abjad.Markup(
        [
            abjad.MarkupCommand("fontsize", -2.4),
            abjad.StringContactPoint(position).markup,
        ],
        direction="up",
    )


def put_gong_to_separate_vox(nth_bar: int, nth_item: int, staff: abjad.Staff) -> None:
    event2separate = abjad.mutate(staff[nth_bar][nth_item]).copy()
    staff[nth_bar][nth_item] = abjad.Container(
        [
            abjad.Voice(
                [
                    abjad.Note(
                        event2separate.written_pitches[0],
                        event2separate.written_duration,
                    )
                ]
            ),
            abjad.Voice(
                [
                    abjad.Chord(
                        event2separate.written_pitches[1:],
                        event2separate.written_duration,
                    )
                ]
            ),
        ],
        simultaneous=True,
    )
    for text in (
        r'\set Staff.ottavation = #"8vb"',
        r"\once \override Staff.OttavaBracket.direction = #DOWN",
        r"\set Voice.middleCPosition = #(+ 6 7)",
    ):
        abjad.attach(
            abjad.LilyPondLiteral(text, format_slot="before"),
            staff[nth_bar][nth_item][0][0],
        )

    for text in (
        r"\unset Staff.ottavation",
        r"\unset Voice.middleCPosition",
    ):
        abjad.attach(
            abjad.LilyPondLiteral(text, format_slot="after"),
            staff[nth_bar][nth_item][0][0],
        )
