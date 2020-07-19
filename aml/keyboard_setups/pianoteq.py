"""Module for the algorithmic live variation of the pianoteq synth."""

import random

import pyo

from mu.utils import tools


class Modulator(object):
    _no_pitch_bending = 8192

    def __init__(
        self, trigger: pyo.Trig, server: pyo.Server, max_pitch_bend_size: int = 350
    ):
        def pitch_bend_trigger():
            gliss_duration = random.randint(70, 300)  # in miliseconds
            gliss_size = random.randint(
                self._no_pitch_bending - max_pitch_bend_size,
                self._no_pitch_bending + max_pitch_bend_size,
            )
            self.interpolation_trigger(
                gliss_size,
                self._no_pitch_bending,
                gliss_duration,
                lambda value, time_stamp: self.server.bendout(
                    value, channel=0, timestamp=time_stamp
                ),
            )

        def make_ctl_trigger(
            attribute_name: str,
            minval: int,
            maxval: int,
            mindur: int,
            maxdur: int,
            ctl_number: int,
        ):
            duration = random.randint(mindur, maxdur)  # in miliseconds
            value1 = random.randint(minval, maxval)
            self.interpolation_trigger(
                getattr(self, attribute_name),
                value1,
                duration,
                lambda value, time_stamp: self.server.ctlout(
                    ctl_number, value, channel=0, timestamp=time_stamp
                ),
            )
            setattr(self, attribute_name, value1)

        def make_pedal_trigger(attribute_name: str, likelihood: float, ctl_number: int):
            if random.random() <= likelihood:
                value1 = 127
            else:
                value1 = 0

            self.interpolation_trigger(
                getattr(self, attribute_name),
                value1,
                1,
                lambda value, time_stamp: self.server.ctlout(
                    ctl_number, value, channel=0, timestamp=time_stamp
                ),
            )
            setattr(self, attribute_name, value1)

        def modulator():
            pitch_bend_trigger()
            make_ctl_trigger("blooming_energy", 10, 60, 50, 100, 41)
            make_ctl_trigger("blooming_inerita", 30, 100, 5, 10, 42)
            make_pedal_trigger("rattle_pedal", 0.3, 57)
            make_pedal_trigger("buff_stop_pedal", 0.3, 58)
            make_pedal_trigger("mozart_rail", 0.3, 67)

        self.blooming_energy = 10
        self.blooming_inerita = 30
        self.rattle_pedal = 0
        self.buff_stop_pedal = 0
        self.mozart_rail = 0

        self.trigger = trigger
        self.server = server

        # turning off sustain pedal
        self.server.ctlout(53, 127, channel=0, timestamp=0)

        self.modulator = pyo.TrigFunc(self.trigger, modulator)

    def interpolation_trigger(self, value0: int, value1: int, duration: int, function):
        if duration > 0:
            if value0 != value1:
                nsteps = abs(value0 - value1)

                timestamps = tuple(range(duration))

                if value0 > value1:
                    steps_in_between = tuple(reversed(range(value1, value0)))

                else:
                    steps_in_between = tuple(range(value0, value1))

                if nsteps > duration:
                    steps_in_between = tuple(
                        steps_in_between[idx]
                        for idx in tools.accumulate_from_zero(
                            tools.euclid(nsteps, duration)
                        )[:-1]
                    )

                elif nsteps < duration:
                    timestamps = tuple(
                        timestamps[idx]
                        for idx in tools.accumulate_from_zero(
                            tools.euclid(duration, nsteps)
                        )[:-1]
                    )

                for time_stamp, value in zip(timestamps, steps_in_between):
                    function(value, time_stamp)

                function(value1, time_stamp + 1)
