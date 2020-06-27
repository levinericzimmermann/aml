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
            if random.random() > 0.5:
                shall_pass = True
            else:
                shall_pass = False
        else:
            shall_pass = True

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
