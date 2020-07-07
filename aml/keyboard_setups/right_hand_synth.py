import abc
import json
import logging
import itertools
import random

import pyo


# map instrument name to particular channel.
# can be changed dynamically before program start if new setup requires different mapping.
INSTRUMENT2CHANNEL_MAPPING = {"violin": 0, "viola": 1, "cello": 2}

try:
    with open("midi_note2freq_and_instrument_mapping.json", "r") as f:
        MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING = {
            int(key): (float(item[0]), item[1]) for key, item in json.load(f).items()
        }
except FileNotFoundError:
    with open(
        "aml/keyboard_setups/midi_note2freq_and_instrument_mapping.json", "r"
    ) as f:
        MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING = {
            int(key): (float(item[0]), item[1]) for key, item in json.load(f).items()
        }


class Generator(abc.ABC):
    def __init__(self, freq: float, mul: float = 1):
        self.freq = freq
        self.mul = mul

    @abc.abstractmethod
    def out(self, chn: int):
        raise NotImplementedError

    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError


class SineGenerator(Generator):
    def __init__(self, freq: float):
        self.fader = pyo.Fader(fadein=0.5, fadeout=0.5)
        self.lfoo0 = pyo.LFO(freq=0.01, mul=1, type=3)
        self.lfoo1 = pyo.Sine(freq=0.02, mul=1)
        self.lfo = pyo.Sine(freq=self.lfoo0 + self.lfoo1, mul=1)
        self.generator = pyo.SineLoop(
            freq=freq, feedback=0.015 + ((1 + self.lfo) * 0.025), mul=self.fader
        )

    @property
    def mul(self) -> float:
        return self.fader.mul

    @mul.setter
    def mul(self, value: float):
        self.fader.mul = value

    def out(self, chnl: int = 0, dur: float = 0, delay: float = 0):
        # randomize parameters for a more lively sound
        fadein_time = random.uniform(0.35, 1.5)
        self.lfoo0.freq = random.uniform(0.01, 0.6)
        self.lfoo1.freq = random.uniform(0.01, 0.5)
        self.lfoo0.mul = random.uniform(0.5, 1.2)
        self.lfoo1.mul = random.uniform(0.5, 1.2)
        self.lfo.mul = random.uniform(0.5, 1)

        self.fader.setFadein(fadein_time)

        # start all lfo and fader
        self.fader.play(dur=dur, delay=delay)
        self.lfoo0.play(dur=dur, delay=delay)
        self.lfoo1.play(dur=dur, delay=delay)
        self.lfo.play(dur=dur, delay=delay)

        # return & start actual generator
        return self.generator.out(chnl=chnl, dur=dur, delay=delay)

    def stop(self, wait: float = None):
        fadeout_time = random.uniform(0.5, 1.2)
        self.fader.setFadeout(fadeout_time)
        self.fader.stop(wait=wait)

        waiting_time = fadeout_time + wait
        self.lfoo0.stop(wait=waiting_time)
        self.lfoo1.stop(wait=waiting_time)
        self.lfo.stop(wait=waiting_time)
        return self.generator.stop(wait=waiting_time)


class RightHandSynth(object):
    _n_voices = 10
    _first_midi_note = min(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)
    _last_midi_note = max(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)
    _midi_note2frequency = {
        mn: freq_and_instrument[0]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }
    _midi_note2channel = {
        mn: INSTRUMENT2CHANNEL_MAPPING[freq_and_instrument[1]]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    def __init__(self):
        def trigger_on_function(voice: int) -> None:
            midi_note = int(self.notes["pitch"].get(all=True)[voice])
            velocity = self.notes["velocity"].get(all=True)[voice] * 0.35
            info = "receive note on msg with voice: "
            info += "'{}', midi-pitch'{}' and velocity: '{}'".format(
                voice, midi_note, velocity
            )
            logging.info(info)
            try:
                generator_name = self.get_nth_generator(midi_note)
            except KeyError:
                logging.info(
                    "No pyo generator has been specified for midi input {}".format(
                        midi_note
                    )
                )
                return

            if velocity > 0:
                getattr(self, generator_name).mul = velocity
                getattr(self, generator_name).out(self._midi_note2channel[midi_note])

        def trigger_off_function(voice: int) -> None:
            midi_note = int(self.notes["pitch"].get(all=True)[voice])
            try:
                generator_name = self.last_generator_per_midi_note[midi_note]
            except KeyError:
                logging.info(
                    "No pyo generator has been specified for midi input {}".format(
                        midi_note
                    )
                )
                return

            getattr(self, generator_name).stop()

        self.last_generator_per_midi_note = {
            midi_note: None
            for midi_note in range(self._first_midi_note, self._last_midi_note + 1)
        }

        self.available_generators_per_midi_note = self.assign_generator_per_midi_note()

        self.notes = pyo.Notein(
            poly=self._n_voices,
            first=self._first_midi_note,
            last=self._last_midi_note,
            channel=0,
        )
        self.trigger_on = pyo.TrigFunc(
            self.notes["trigon"], trigger_on_function, arg=list(range(self._n_voices))
        )
        self.trigger_off = pyo.TrigFunc(
            self.notes["trigoff"], trigger_off_function, arg=list(range(self._n_voices))
        )

    def assign_generator_per_midi_note(self) -> dict:
        available_generator_per_midi_note = {}
        for midi_note, frequency in self._midi_note2frequency.items():
            gen = []
            for name, generator in (("sine", SineGenerator),):
                name = "{}{}".format(name, midi_note)
                setattr(self, name, generator(freq=frequency))
                gen.append(name)

            available_generator_per_midi_note.update({midi_note: tuple(gen)})

        return {
            midi_note: itertools.cycle(generators)
            for midi_note, generators in available_generator_per_midi_note.items()
        }

    def get_nth_generator(self, midi_note: int) -> str:
        choosen_generator = next(self.available_generators_per_midi_note[midi_note])
        self.last_generator_per_midi_note[midi_note] = choosen_generator
        return choosen_generator
