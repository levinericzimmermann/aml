"""This module handles the sound synthesis of the midi keyboard."""

import abc
import json
import logging
import itertools
import random
import time

import pyo

from mu.utils import tools

import settings


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
        return self.generator.play(dur=dur, delay=delay)

    def stop(self, wait: float = None):
        fadeout_time = random.uniform(0.5, 1.2)
        self.fader.setFadeout(fadeout_time)
        self.fader.stop(wait=wait)

        if wait:
            waiting_time = fadeout_time + wait
        else:
            waiting_time = fadeout_time

        self.lfoo0.stop(wait=waiting_time)
        self.lfoo1.stop(wait=waiting_time)
        self.lfo.stop(wait=waiting_time)
        return self.generator.stop(wait=waiting_time)


class GongGenerator(Generator):
    _fadeout_time = 0.01

    def __init__(self, path: str, mixer_idx_left: int, mixer_idx_right: int) -> None:
        self.mixer_idx_left = mixer_idx_left
        self.mixer_idx_right = mixer_idx_right
        self.fader = pyo.Fader(fadein=0.02, fadeout=self._fadeout_time)
        self.table_left = pyo.SndTable(path, chnl=0)
        self.table_right = pyo.SndTable(path, chnl=1)
        self.freq = self.table_left.getRate()
        self.generator_left = pyo.TableRead(
            table=self.table_left, freq=self.freq, mul=self.fader
        )
        self.generator_right = pyo.TableRead(
            table=self.table_right, freq=self.freq, mul=self.fader
        )

    @property
    def mul(self) -> float:
        return self.fader.mul

    @mul.setter
    def mul(self, value: float):
        self.fader.mul = value

    def out(self, chnl: int = 0, dur: float = 0, delay: float = 0):
        # start fader
        self.fader.play(dur=dur, delay=delay)

        # return & start actual generator
        self.generator_left.play(dur=dur, delay=delay)
        return self.generator_right.play(dur=dur, delay=delay)

    def stop(self):
        self.fader.stop()
        self.generator_left.stop(wait=self._fadeout_time)
        return self.generator_right.stop(wait=self._fadeout_time)


class MidiSynth(object):
    _n_voices = 10
    _first_midi_note = min(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)
    _last_midi_note = max(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)
    _first_gong_midi_note = 21
    _last_gong_midi_note = 21 + 14

    _midi_note2frequency = {
        mn: freq_and_instrument[0]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    _midi_note2instrument = {
        mn: freq_and_instrument[1]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    _midi_note2channel = {
        mn: settings.SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING[freq_and_instrument[1]]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    _available_sine_generators = (("sine", SineGenerator),)

    def __init__(self):
        self.previous_hauptstimme_instrument = set([])
        self._last_trigger_time = time.time()
        self.instrument_change_trigger = pyo.Trig()

        self.pianoteq_trigger = pyo.Trig()

        self.sine_mixer = pyo.Mixer(outs=3, chnls=1, mul=0.3)
        self.gong_mixer = pyo.Mixer(outs=4, chnls=1, time=0.045, mul=1)

        # get gui of both mixers
        self.sine_mixer.ctrl(title="transducer")
        self.gong_mixer.ctrl(title="gong")

        self.gong_spatialisation_cycle = self._make_gong_spatialisation_cycle()

        self.last_generator_per_midi_note = {
            midi_note: None
            for midi_note in range(self._first_midi_note, self._last_midi_note + 1)
        }

        self.available_generators_per_midi_note = self.assign_generator_per_midi_note()

        # sending all transducer and gong inputs out
        for mixer, mixer2channel_mapping in (
            (self.sine_mixer, settings.SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING),
            (self.gong_mixer, settings.GONG_MIXER2CHANNEL_MAPPING),
        ):
            [mixer[i][0].play() for i in mixer2channel_mapping.values()]

        self.notes = pyo.Notein(
            poly=self._n_voices,
            first=self._first_gong_midi_note,
            last=self._last_midi_note,
            channel=0,
        )
        self.trigger_on = pyo.TrigFunc(
            self.notes["trigon"],
            self._trigger_on_function,
            arg=list(range(self._n_voices)),
        )
        self.trigger_off = pyo.TrigFunc(
            self.notes["trigoff"],
            self._trigger_off_function,
            arg=list(range(self._n_voices)),
        )

    @staticmethod
    def _log_trigger_info(voice: int, midi_note: int, velocity: float) -> None:
        info = "receive note on msg with voice: "
        info += "'{}', midi-pitch'{}' and velocity: '{}'".format(
            voice, midi_note, velocity
        )
        logging.info(info)

    def _trigger_on_function(self, voice: int) -> None:
        midi_note = int(self.notes["pitch"].get(all=True)[voice])
        velocity = self.notes["velocity"].get(all=True)[voice]
        self._log_trigger_info(voice, midi_note, velocity)
        try:
            generator_name = self.get_nth_generator(midi_note)
        except KeyError:
            # than it must be the pianoteq part
            self.pianoteq_trigger.play()
            return

        if velocity > 0:
            getattr(self, generator_name).mul = velocity

            delay = 0
            if isinstance(getattr(self, generator_name), GongGenerator):
                if getattr(self, generator_name).generator_left.isPlaying():
                    getattr(self, generator_name).stop()
                self.spatialise_gong(getattr(self, generator_name))
                delay = 0.015

            else:
                # than the generator must be part of the transducer sounds
                current_time = time.time()

                # only override the previous hauptstimme attribute if the previous signal
                # is more than 250 miliseconds away for avoiding confused values when
                # chords are played.

                responsible_instrument = self._midi_note2instrument[midi_note]
                if responsible_instrument not in self.previous_hauptstimme_instrument:
                    if current_time - self._last_trigger_time > 0.25:
                        self.previous_hauptstimme_instrument = set(
                            [responsible_instrument]
                        )

                    else:
                        self.previous_hauptstimme_instrument.add(responsible_instrument)

                    self.instrument_change_trigger.play()
                    self._last_trigger_time = current_time

            getattr(self, generator_name).out(delay=delay)

    def _trigger_off_function(self, voice: int) -> None:
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

        if not isinstance(getattr(self, generator_name), GongGenerator):
            getattr(self, generator_name).stop()

    def spatialise_gong(self, generator: GongGenerator) -> None:
        spats = next(self.gong_spatialisation_cycle)
        for spat, idx in zip(
            spats, (generator.mixer_idx_left, generator.mixer_idx_right)
        ):
            for output_idx, amplitude in enumerate(spat):
                self.gong_mixer.setAmp(idx, output_idx, amplitude)
        self.gong_mixer.mul = 1

    @staticmethod
    def _make_gong_spatialisation_cycle() -> itertools.cycle:
        def convert_vector2volume_per_channel(vector: tuple) -> tuple:
            n_items = sum(vector)
            return tuple(item / n_items for item in vector)

        graycode = tools.graycode(4, 2)
        combinations_for_left_and_right_channel = tuple(zip(graycode, graycode[6:]))
        spat_cycle = []
        for spat_left, spat_right in combinations_for_left_and_right_channel * 2:
            # ignore vector (0, 0, 0, 0)
            if any(spat_left) and any(spat_right):
                spat_cycle.append(
                    tuple(
                        convert_vector2volume_per_channel(vec)
                        for vec in (spat_left, spat_right)
                    )
                )

        return itertools.cycle(spat_cycle)

    def _assign_transducer_generator_per_midi_note(self) -> dict:
        available_generator_per_midi_note = {}
        nth_sine_input = 0
        for midi_note, frequency in self._midi_note2frequency.items():
            gen = []
            for name, generator in self._available_sine_generators:
                name = "{}{}".format(name, midi_note)
                setattr(self, name, generator(freq=frequency))

                self.sine_mixer.addInput(nth_sine_input, getattr(self, name).generator)
                self.sine_mixer.setAmp(
                    nth_sine_input, self._midi_note2channel[midi_note], 1
                )
                nth_sine_input += 1

                gen.append(name)

            available_generator_per_midi_note.update({midi_note: tuple(gen)})

        return available_generator_per_midi_note

    def _assign_gong_generator_per_midi_note(self) -> dict:
        available_generator_per_midi_note = {}
        path = "kempul_samples/adapted"
        gong_indices = 0
        for midi_note in range(self._first_gong_midi_note, self._last_gong_midi_note):
            nth_gong = midi_note - self._first_gong_midi_note
            name = "gong{}".format(midi_note)
            local_path = "{}/{}.wav".format(path, nth_gong)
            gong_idx_left, gong_idx_right = gong_indices, gong_indices + 1
            setattr(
                self, name, GongGenerator(local_path, gong_idx_left, gong_idx_right)
            )
            self.gong_mixer.addInput(gong_idx_left, getattr(self, name).generator_left)
            self.gong_mixer.addInput(
                gong_idx_right, getattr(self, name).generator_right
            )
            available_generator_per_midi_note.update({midi_note: (name,)})
            gong_indices += 2

        return available_generator_per_midi_note

    def assign_generator_per_midi_note(self) -> dict:
        available_generator_per_midi_note = {}
        available_generator_per_midi_note.update(
            self._assign_transducer_generator_per_midi_note()
        )
        available_generator_per_midi_note.update(
            self._assign_gong_generator_per_midi_note()
        )
        return {
            midi_note: itertools.cycle(generators)
            for midi_note, generators in available_generator_per_midi_note.items()
        }

    def get_nth_generator(self, midi_note: int) -> str:
        choosen_generator = next(self.available_generators_per_midi_note[midi_note])
        self.last_generator_per_midi_note[midi_note] = choosen_generator
        return choosen_generator
