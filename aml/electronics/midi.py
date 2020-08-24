"""This module handles the sound synthesis of the midi keyboard."""

import abc
import itertools
import json
import logging
import random
import time

import pyo

from mu.utils import tools

try:
    import settings
except ImportError:
    from aml.electronics import settings


try:
    with open("midi_note2freq_and_instrument_mapping.json", "r") as f:
        MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING = {
            int(key): (float(item[0]), item[1]) for key, item in json.load(f).items()
        }
except FileNotFoundError:
    with open("aml/electronics/midi_note2freq_and_instrument_mapping.json", "r") as f:
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
    min_vol = 0.1
    max_vol = 0.97

    def __init__(self, freq: float):
        self.fader = pyo.Fader(fadein=0.5, fadeout=0.5)
        self.lfoo0 = pyo.LFO(freq=0.01, mul=1, type=3)
        self.lfoo1 = pyo.Sine(freq=0.02, mul=1)
        self.lfo = pyo.Sine(freq=self.lfoo0 + self.lfoo1, mul=1)
        self.generator = pyo.SineLoop(
            freq=freq, feedback=0.015 + ((1 + self.lfo) * 0.025), mul=self.fader
        )
        self.generator.stop()
        self.stop(fadeout=False)
        self._mul = self.max_vol
        self._mul_setter = pyo.Trig()

    @property
    def mul(self) -> float:
        return self._mul

    @mul.setter
    def mul(self, value: float):
        self._mul = tools.scale((0, 1, value), self.min_vol, self.max_vol)[-1]

    def out(self, dur: float = 0, delay: float = 0):
        def set_fader_mul():
            self.fader.mul = self.mul

        self._mul_trig_func = pyo.TrigFunc(self._mul_setter, set_fader_mul)

        # randomize parameters for a more lively sound
        fadein_time = random.uniform(0.35, 1.5)
        self.lfoo0.freq = random.uniform(0.01, 0.6)
        self.lfoo1.freq = random.uniform(0.01, 0.5)
        self.lfoo0.mul = random.uniform(0.5, 1.2)
        self.lfoo1.mul = random.uniform(0.5, 1.2)
        self.lfo.mul = random.uniform(0.5, 1)

        self.fader.setFadein(fadein_time)

        self._mul_setter.play(delay=delay)

        # start all lfo and fader
        self.fader.play(dur=dur, delay=delay)
        self.lfoo0.play(dur=dur, delay=delay)
        self.lfoo1.play(dur=dur, delay=delay)
        self.lfo.play(dur=dur, delay=delay)

        # return & start actual generator
        self.generator.play(dur=dur, delay=delay)

    def stop(self, wait: float = 0, fadeout: bool = True):
        if fadeout:
            fadeout_time = random.uniform(0.5, 0.9)
            self.fader.setFadeout(fadeout_time)
            self.fader.stop(wait=wait)

            if wait:
                waiting_time = fadeout_time + wait
            else:
                waiting_time = fadeout_time
        else:
            waiting_time = wait

        self.lfoo0.stop(wait=waiting_time)
        self.lfoo1.stop(wait=waiting_time)
        self.lfo.stop(wait=waiting_time)
        self.generator.stop(wait=waiting_time)


class MonophonGongGenerator(Generator):
    _fadeout_time = 0.03
    min_vol = 0.15
    max_vol = 1

    def __init__(self, mixer_idx_left: int, mixer_idx_right: int) -> None:
        self.mixer_idx_left = mixer_idx_left
        self.mixer_idx_right = mixer_idx_right
        self.fader = pyo.Fader(fadein=0.005, fadeout=self._fadeout_time)
        dummy_table = pyo.SquareTable(order=1)
        self.generator_left = pyo.TableRead(table=dummy_table, mul=self.fader)
        self.generator_right = pyo.TableRead(table=dummy_table, mul=self.fader)
        self._midi_note_to_tables = {}
        self.trigger0 = pyo.Trig()
        self.trigger1 = pyo.Trig()
        self._mul = self.max_vol

    @property
    def mul(self) -> float:
        return self._mul

    @mul.setter
    def mul(self, value: float):
        self._mul = tools.scale((0, 1, value), self.min_vol, self.max_vol)[-1]

    def add_midi_note_to_sample_path(self, midi_note: int, sample_path: str) -> None:
        table_left = pyo.SndTable(sample_path, chnl=0)
        table_right = pyo.SndTable(sample_path, chnl=1)
        self._midi_note_to_tables.update({midi_note: (table_left, table_right)})

    def out(self, midi_note: int, dur: float = 0, delay: float = 0):
        def kill_generator():
            self.generator_left.stop()
            self.generator_right.stop()

        def set_generator():
            table_left, table_right = self._midi_note_to_tables[midi_note]
            self.generator_left.setTable(table_left)
            self.generator_right.setTable(table_right)
            self.generator_left.setFreq(table_left.getRate())
            self.generator_right.setFreq(table_right.getRate())

            self.fader.mul = float(self.mul)

            self.fader.play(dur=dur, delay=0.001)
            self.generator_left.play(dur=dur, delay=0.002)
            self.generator_right.play(dur=dur, delay=0.002)

        self.trigger_func0 = pyo.TrigFunc(self.trigger0, kill_generator)
        self.trigger_func1 = pyo.TrigFunc(self.trigger1, set_generator)
        self.trigger0.play(delay=delay)
        self.trigger1.play(delay=delay + 0.0001)

    def stop(self):
        self.fader.stop()


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

    def __init__(self, server: pyo.Server, midi_data_logger):
        self.midi_data_logger = midi_data_logger
        self.server = server
        self.previous_hauptstimme_instrument = set([])
        self._last_trigger_time = time.time()
        self.instrument_change_trigger = pyo.Trig()

        self.pianoteq_trigger = pyo.Trig()

        self.sine_mixer = pyo.Mixer(outs=3, chnls=1, mul=0.3)
        self.gong_mixer = pyo.Mixer(outs=4, chnls=1, time=0.05, mul=1)
        self.gong_mixer.mul = 1

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
            poly=self._n_voices, last=self._last_midi_note, channel=0,
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

        # for attr in dir(self):
        #     getattr(self, attr).stop()

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
        self.midi_data_logger.load_note_on_data(voice, midi_note, velocity)
        try:
            generator_name = self.get_nth_generator(midi_note)
        except KeyError:
            # than it must be the pianoteq part
            self.pianoteq_trigger.play()
            self.server.noteout(midi_note, int(velocity * 127))
            return

        if velocity > 0:
            getattr(self, generator_name).mul = velocity

            is_gong = False
            if isinstance(getattr(self, generator_name), MonophonGongGenerator):
                if getattr(self, generator_name).generator_left.isPlaying():
                    getattr(self, generator_name).stop()
                    delay = getattr(self, generator_name)._fadeout_time + 0.001
                else:
                    delay = 0

                is_gong = True

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

            if is_gong:
                self.spatialise_gong(getattr(self, generator_name), delay)
                getattr(self, generator_name).out(delay=delay, midi_note=midi_note)
            else:
                getattr(self, generator_name).out()

    def _trigger_off_function(self, voice: int) -> None:
        midi_note = int(self.notes["pitch"].get(all=True)[voice])

        try:
            generator_name = self.last_generator_per_midi_note[midi_note]
        except KeyError:
            # than it must be the pianoteq part
            self.server.makenote(midi_note, 0, 0)
            return

        if not isinstance(getattr(self, generator_name), MonophonGongGenerator):
            getattr(self, generator_name).stop()

    def spatialise_gong(self, generator: MonophonGongGenerator, delay: float) -> None:
        def spatialise():
            spats = next(self.gong_spatialisation_cycle)
            for spat, idx in zip(
                spats, (generator.mixer_idx_left, generator.mixer_idx_right)
            ):
                for output_idx, amplitude in enumerate(spat):
                    self.gong_mixer.setAmp(idx, output_idx, amplitude)

        self._gong_trigfun = pyo.TrigFunc(generator.trigger1, spatialise)

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

    # def _assign_gong_generator_per_midi_note(self) -> dict:
    #     available_generator_per_midi_note = {}
    #     path = "kempul_samples/adapted"
    #     gong_indices = 0
    #     for midi_note in range(self._first_gong_midi_note, self._last_gong_midi_note):
    #         nth_gong = midi_note - self._first_gong_midi_note
    #         name = "gong{}".format(midi_note)
    #         local_path = "{}/{}.wav".format(path, nth_gong)
    #         gong_idx_left, gong_idx_right = gong_indices, gong_indices + 1
    #         setattr(
    #             self, name, GongGenerator(local_path, gong_idx_left, gong_idx_right)
    #         )
    #         self.gong_mixer.addInput(gong_idx_left, getattr(self, name).generator_left)
    #         self.gong_mixer.addInput(
    #             gong_idx_right, getattr(self, name).generator_right
    #         )
    #         available_generator_per_midi_note.update({midi_note: (name,)})
    #         gong_indices += 2

    #     return available_generator_per_midi_note

    def _assign_gong_generator_per_midi_note(self) -> dict:
        available_generator_per_midi_note = {}
        path = "kempul_samples/adapted"
        gong_idx_left, gong_idx_right = 0, 1
        gong_generator = MonophonGongGenerator(gong_idx_left, gong_idx_right)
        name = "monophon_gong"
        setattr(self, name, gong_generator)
        self.gong_mixer.addInput(gong_idx_left, getattr(self, name).generator_left)
        self.gong_mixer.addInput(gong_idx_right, getattr(self, name).generator_right)

        for midi_note in range(self._first_gong_midi_note, self._last_gong_midi_note):
            nth_gong = midi_note - self._first_gong_midi_note
            local_path = "{}/{}.wav".format(path, nth_gong)
            gong_generator.add_midi_note_to_sample_path(midi_note, local_path)
            available_generator_per_midi_note.update({midi_note: (name,)})

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
