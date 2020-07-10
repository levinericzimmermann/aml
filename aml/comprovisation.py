import functools
import operator
import itertools
import random

from mutools import attachments
from mutools import lily


def process_comprovisation_attachments(novent_line: lily.NOventLine) -> lily.NOventLine:
    new_novent_line = lily.NOventLine([])
    for novent in novent_line.copy():
        if novent.optional:
            # perhaps it is more likely that an optional tone get played by the musicians
            # than that it won't get played.
            if random.random() > 0.38:
                shall_pass = True
            else:
                shall_pass = False
        else:
            shall_pass = True

        if novent.optional_some_pitches:
            choosen_pitches = []
            for pitch_idx, pitch in enumerate(sorted(novent.pitch)):
                if pitch_idx in novent.optional_some_pitches.optional_pitch_indices:
                    if random.random() > 0.4:
                        choosen_pitches.append(pitch)
                else:
                    choosen_pitches.append(pitch)

            novent.pitch = choosen_pitches

        if shall_pass:
            if isinstance(novent.choose, attachments.ChooseOne):
                novent.pitch = [random.choice(novent.pitch)]

            elif isinstance(novent.choose, attachments.Choose):
                possible_choices = functools.reduce(
                    operator.add,
                    tuple(
                        tuple(itertools.combinations(novent.pitch, n + 1))
                        for n in range(len(novent.pitch))
                    ),
                )
                novent.pitch = list(
                    possible_choices[random.choice(range(len(possible_choices)))]
                )

            new_novent_line.append(novent)

        else:
            new_novent_line.append(
                lily.NOvent(
                    pitch=[],
                    tempo=novent.tempo,
                    duration=novent.duration,
                    delay=novent.delay,
                )
            )

    return new_novent_line
