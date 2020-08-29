"""This module handles the sound synthesis of the midi keyboard.

(except for its pianoteq part)
"""

import abc
import itertools
import json
import os
import random
import time

import numpy as np

import natsort
import pyo

from mu.utils import infit
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


#########################################################################
#           abstract classes for writing midi-synth-classes             #
#########################################################################


class PolySynth(object):
    """PolySynth class for midi-based keyboard."""

    def __init__(self, n_voices: int):
        self._voice_cycle = itertools.cycle(range(n_voices))
        self._generators = tuple(self._generator_class() for _ in range(n_voices))
        self.mixer = pyo.Mixer(1, chnls=self._nchnls_per_generator)

        for nth_gen, generator in enumerate(self.generators):
            self.mixer.addInput(nth_gen, generator.generator)
            self.mixer.setAmp(nth_gen, 0, 1)

    @abc.abstractproperty
    def _generator_class(self):
        raise NotImplementedError

    @abc.abstractproperty
    def _nchnls_per_generator(self) -> int:
        raise NotImplementedError

    @abc.abstractproperty
    def _available_types_infit(self) -> infit.InfIt:
        raise NotImplementedError

    @property
    def generators(self) -> tuple:
        return self._generators

    def out(self, midi_note: int, velocity: float) -> None:
        self.generators[next(self._voice_cycle)].out(
            midi_note, velocity, next(self._available_types_infit)
        )

    def stop(self, midi_note: int) -> None:
        for gen in self.generators:
            if gen.midi_note == midi_note and gen.generator.isPlaying():
                gen.stop()


class PolySynthGenerator(object):
    def __init__(self) -> None:
        self._last_assigned_midi_note = None
        self._last_generator = 0
        self._available_generators = self._make_available_generators()
        self.generator = sum([gen.generator for gen in self._available_generators])

    @property
    def midi_note(self) -> int:
        return self._last_assigned_midi_note

    @abc.abstractmethod
    def _make_available_generators(self) -> tuple:
        raise NotImplementedError

    def out(self, midi_note: int, velocity: float, synth_type: int,) -> None:
        self.stop()
        self._available_generators[synth_type].out(midi_note, velocity)
        self._last_assigned_midi_note = midi_note
        self._last_generator = synth_type

    def stop(self) -> None:
        self._available_generators[self._last_generator].stop()


#########################################################################
#                   transducer synthesizer                              #
#########################################################################


class SineGenerator(object):
    min_vol = 0.1
    max_vol = 0.97

    def __init__(self):
        self.fader = pyo.Fader(fadein=0.5, fadeout=0.5)
        self.lfoo0 = pyo.LFO(freq=0.01, mul=1, type=3)
        self.lfoo1 = pyo.Sine(freq=0.02, mul=1)
        self.lfo = pyo.Sine(freq=self.lfoo0 + self.lfoo1, mul=1)
        self.generator = pyo.SineLoop(
            freq=100, feedback=0.015 + ((1 + self.lfo) * 0.025), mul=[self.fader, 0, 0]
        )
        self.generator.stop()
        self.stop()
        self._mul = self.max_vol
        self._mul_setter = pyo.Trig()

    @property
    def mul(self) -> float:
        return self._mul

    @mul.setter
    def mul(self, value: float):
        self._mul = tools.scale((0, 1, value), self.min_vol, self.max_vol)[-1]

    def out(self, freq: float, velocity: float, channel: int):
        def set_fader_mul():
            self.fader.mul = self.mul

        self._mul_trig_func = pyo.TrigFunc(self._mul_setter, set_fader_mul)

        self.generator.setFreq(freq)

        # randomize parameters for a more lively sound
        fadein_time = random.uniform(0.35, 1.5)
        self.lfoo0.freq = random.uniform(0.01, 0.6)
        self.lfoo1.freq = random.uniform(0.01, 0.5)
        self.lfoo0.mul = random.uniform(0.5, 1.2)
        self.lfoo1.mul = random.uniform(0.5, 1.2)
        self.lfo.mul = random.uniform(0.5, 1)

        self.fader.setFadein(fadein_time)

        self._mul_setter.play()

        # start all lfo and fader
        self.fader.play()
        self.lfoo0.play()
        self.lfoo1.play()
        self.lfo.play()

        # return & start actual generator
        self.generator.mul = [self.fader if idx == channel else 0 for idx in range(3)]
        self.generator.play()

    def stop(self):
        fadeout_time = random.uniform(0.5, 0.9)
        self.fader.setFadeout(fadeout_time)
        self.fader.stop()

        waiting_time = fadeout_time

        self.lfoo0.stop(wait=waiting_time)
        self.lfoo1.stop(wait=waiting_time)
        self.lfo.stop(wait=waiting_time)
        self.generator.stop(wait=waiting_time)


class TransducerSynthGenerator(PolySynthGenerator):
    def _make_available_generators(self) -> tuple:
        return (SineGenerator(),)

    def out(
        self,
        midi_note: int,
        velocity: float,
        synth_type: int,
        freq: float,
        channel: int,
    ) -> None:
        self.stop()

        self._available_generators[synth_type].out(freq, velocity, channel)

        self._last_assigned_midi_note = midi_note
        self._last_generator = synth_type


class TransducerSynth(PolySynth):
    # repeating sine wave
    _available_types_infit = infit.Cycle((0,))

    _midi_note2frequency = {
        mn: freq_and_instrument[0]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }
    _midi_note2channel = {
        mn: settings.SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING[freq_and_instrument[1]]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    _nchnls_per_generator = 3
    _generator_class = TransducerSynthGenerator

    def out(self, midi_note: int, velocity: float) -> None:
        nth_voice = next(self._voice_cycle)
        self.generators[nth_voice].out(
            midi_note,
            velocity,
            next(self._available_types_infit),
            self._midi_note2frequency[midi_note],
            self._midi_note2channel[midi_note],
        )


#########################################################################
#                       gong synthesizer                                #
#########################################################################


class _GongSamplerMetaClass(type):
    """This Metaclass handles the generation of soundtables.

    In this way soundtables can be shared between different instances of
    the same class and don't have to be generated for each individual
    new object.
    """

    def __new__(cls, name, bases, dct):
        instance = super().__new__(cls, name, bases, dct)

        try:
            sample_path = instance._path
        except AttributeError:
            msg = "Class have to have the '_path' class attribute!"
            raise NotImplementedError(msg)

        tables_per_index = []
        for sf in natsort.natsorted(os.listdir(sample_path)):
            if sf[-3:] == "wav":
                # hard coded: the expected samples have to be stereo!
                tables = tuple(
                    pyo.SndTable(path="{}/{}".format(sample_path, sf), chnl=chnl)
                    for chnl in range(2)
                )
                tables_per_index.append(tables)

        instance.snd_tables = tuple(tables_per_index)

        return instance


class GongGenerator(object, metaclass=_GongSamplerMetaClass):
    _fadeout_time = 0.03
    min_vol = 0.14
    max_vol = 1

    _path = "samples/kempul/adapted"

    _first_gong_midi_note = 21
    _last_gong_midi_note = 21 + 14
    _midi_note2index = {
        midi_note: idx
        for idx, midi_note in enumerate(
            range(_first_gong_midi_note, _last_gong_midi_note + 1)
        )
    }

    def __init__(self) -> None:
        self.fader = pyo.Fader(fadein=0.005, fadeout=self._fadeout_time)
        self.trigger1 = pyo.Trig()
        self._mul = self.max_vol
        self.spatialisation = [[pyo.Sig(0) for _ in range(4)] for _ in range(2)]
        self.table_reads = [
            pyo.TableRead(table, freq=table.getRate(),) for table in self.snd_tables[0]
        ]
        self.processed_tables = self.table_reads
        self.spatialised_tables = [
            pyo.Mix(
                signal, voices=4, mul=[self.fader * spat_value for spat_value in spat]
            )
            for signal, spat in zip(self.processed_tables, self.spatialisation)
        ]
        self.generator = self.spatialised_tables[0] + self.spatialised_tables[1]

    @property
    def mul(self) -> float:
        return self._mul

    @mul.setter
    def mul(self, value: float):
        self._mul = tools.scale((0, 1, value), self.min_vol, self.max_vol)[-1]

    def out(self, midi_note: int, velocity: float, spatialisation: tuple) -> None:
        self.stop()

        self.mul = velocity
        self.fader.mul = float(self.mul)

        for snd_chnl, spat in enumerate(spatialisation):
            for spat_chnl, value in enumerate(spat):
                self.spatialisation[snd_chnl][spat_chnl].value = value

        for chnl, table in enumerate(self.snd_tables[self._midi_note2index[midi_note]]):
            self.table_reads[chnl].setFreq(table.getRate())
            self.table_reads[chnl].setTable(table)
            self.table_reads[chnl].play()
            self.processed_tables[chnl].play()
            self.spatialised_tables[chnl].play()

        self.generator.play()
        self.fader.play(delay=0.002)

    def stop(self):
        self.fader.stop()
        for tr, pr_tr, sp_tr in zip(
            self.table_reads, self.processed_tables, self.spatialised_tables
        ):
            tr.stop(wait=self._fadeout_time)
            pr_tr.stop(wait=self._fadeout_time)
            sp_tr.stop(wait=self._fadeout_time)

        self.generator.stop()


class KenongGenerator(GongGenerator):
    min_vol = 0.07
    max_vol = 0.9

    min_filter_freq = 800
    max_filter_freq = 2000
    n_steps = 1000
    filter_scale = tuple(
        map(float, np.geomspace(min_filter_freq, max_filter_freq, n_steps))
    )
    max_value_for_filter = 0.6
    max_max_filter_freq = 3000
    n_filter_stages = 3

    _path = "samples/kenong/adapted"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_tables = [
            pyo.Biquadx(table_read, freq=1000, stages=self.n_filter_stages)
            for table_read in self.table_reads
        ]

    @property
    def mul(self) -> float:
        return self._mul

    @mul.setter
    def mul(self, value: float):
        self._mul = tools.scale((0, 1, value), self.min_vol, self.max_vol)[-1]
        if value <= self.max_value_for_filter:
            filter_freq = self.filter_scale[
                int((value / self.max_value_for_filter) * self.n_steps)
            ]
        else:
            filter_freq = self.max_max_filter_freq

        for process in self.processed_tables:
            process.setFreq(filter_freq)


class BellPlateGenerator(KenongGenerator):
    min_vol = 0.07
    max_vol = 0.8

    _path = "samples/bellplate/adapted"
    n_filter_stages = 5

    min_filter_freq = 500
    max_filter_freq = 1250
    max_value_for_filter = 0.7
    n_steps = 1000
    filter_scale = tuple(
        map(float, np.geomspace(min_filter_freq, max_filter_freq, n_steps))
    )


class GongSynthGenerator(PolySynthGenerator):
    def _make_available_generators(self) -> tuple:
        return (GongGenerator(),)

    def out(
        self, midi_note: int, velocity: float, synth_type: int, spatialisation: tuple
    ) -> None:
        self.stop()
        self._available_generators[synth_type].out(midi_note, velocity, spatialisation)

        self._last_assigned_midi_note = midi_note
        self._last_generator = synth_type

    def stop(self) -> None:
        # self._available_generators[self._last_generator].stop()
        pass


class KenongSynthGenerator(GongSynthGenerator):
    def _make_available_generators(self) -> tuple:
        return (KenongGenerator(), BellPlateGenerator())


class GongSynth(PolySynth):
    # repeating Javanese gong samples
    _available_types_infit = infit.Cycle((0,))
    _generator_class = GongSynthGenerator
    _nchnls_per_generator = 4

    def __init__(self, n_voices: int) -> None:
        super().__init__(n_voices)
        self.spatialisation_cycle = self._make_spatialisation_cycle()

    @staticmethod
    def _make_spatialisation_cycle() -> itertools.cycle:
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

    def out(self, midi_note: int, velocity: float) -> None:
        voice_idx = next(self._voice_cycle)
        self.generators[voice_idx].out(
            midi_note,
            velocity,
            next(self._available_types_infit),
            next(self.spatialisation_cycle),
        )


class KenongSynth(GongSynth):
    _generator_class = KenongSynthGenerator
    _available_types_infit = infit.Cycle((0, 1))


#########################################################################
#               midi synth class that controls everything               #
#########################################################################


class MidiSynth(object):
    _n_voices = 12
    _n_voices_for_gong_synth = 2
    _n_voices_for_kenong_synth = 3
    _n_voices_for_transducer_synth = 6
    _first_midi_note = min(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)
    _last_midi_note = max(MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING)

    _midi_note2instrument = {
        mn: freq_and_instrument[1]
        for mn, freq_and_instrument in MIDI_NOTE2FREQ_AND_INSTRUMENT_MAPPING.items()
    }

    _velocity_range_pianoteq = 127 - settings.MIN_VELOCITY_TO_PIANOTEQ

    def __init__(self, server: pyo.Server, midi_data_logger):
        self.midi_data_logger = midi_data_logger
        self.server = server
        self.previous_hauptstimme_instrument = set([])
        self._last_trigger_time = time.time()
        self.instrument_change_trigger = pyo.Trig()

        self.pianoteq_trigger = pyo.Trig()

        self.sine_mixer = pyo.Mixer(outs=3, chnls=1, mul=0.3)
        self.sine_radio_mixer = pyo.Mixer(outs=4, chnls=1, mul=0.3)
        self.gong_mixer = pyo.Mixer(outs=4, chnls=1, time=0.05, mul=1)
        # self.gong_mixer.mul = 1

        self.transducer_synth = TransducerSynth(self._n_voices_for_transducer_synth)
        self.gong_synth = GongSynth(self._n_voices_for_gong_synth)
        self.kenong_synth = KenongSynth(self._n_voices_for_kenong_synth)

        # sending transducer outputs to sine mixer & sine radio mixer
        for n in range(3):
            signal = self.transducer_synth.mixer[0][n]
            self.sine_mixer.addInput(n, signal)
            self.sine_mixer.setAmp(n, n, 1)

            self.sine_radio_mixer.addInput(n, signal)
            for m in range(4):
                # TODO(which amp?)
                self.sine_mixer.setAmp(n, m, 1)

        # sending gong outputs and kenong outputs to gong mixer
        for n, mixer in enumerate((self.kenong_synth.mixer, self.gong_synth.mixer)):
            added = 4 * n
            for n in range(4):
                signal = mixer[0][n]
                self.gong_mixer.addInput(n + added, signal)
                self.gong_mixer.setAmp(n + added, n, 1)

        # sending all transducer and gong inputs out
        for mixer, mixer2channel_mapping in (
            (self.sine_mixer, settings.SINE_MIXER_INSTRUMENT2CHANNEL_MAPPING),
            (
                self.sine_radio_mixer,
                settings.SINE_TO_RADIO_MIXER_INSTRUMENT2CHANNEL_MAPPING,
            ),
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

        self.sustain_pedal = pyo.Midictl(
            settings.KEYBOARD_PEDAL_CTRL_NUMBER,
            0,
            1,
            init=0,
            channel=settings.KEYBOARD_CHANNEL,
        )

    @staticmethod
    def _get_synth_type(midi_note: int) -> str:
        """hard coded function for detecting the responsible sound area"""
        if midi_note > 20 and midi_note <= 34:
            return "gong"
        elif midi_note >= 71:
            return "transducer"
        else:
            return "pianoteq"

    def _trigger_on_function(self, voice: int) -> None:
        midi_note = int(self.notes["pitch"].get(all=True)[voice])
        velocity = self.notes["velocity"].get(all=True)[voice]
        self.midi_data_logger.load_note_on_data(voice, midi_note, velocity)

        synth_type = self._get_synth_type(midi_note)

        if synth_type == "pianoteq":
            self.pianoteq_trigger.play()
            self.server.noteout(
                midi_note,
                settings.MIN_VELOCITY_TO_PIANOTEQ
                + int(velocity * self._velocity_range_pianoteq),
            )
            return

        elif velocity > 0:
            if synth_type == "transducer":
                responsible_instrument = self._midi_note2instrument[midi_note]
                if responsible_instrument not in self.previous_hauptstimme_instrument:
                    self.previous_hauptstimme_instrument = set([responsible_instrument])

                    self.instrument_change_trigger.play()

                synth = self.transducer_synth

            else:
                is_pedal_active = self.sustain_pedal.get() > 0.5
                if is_pedal_active:
                    synth = self.gong_synth
                else:
                    synth = self.kenong_synth

            synth.out(midi_note, velocity)

    def _trigger_off_function(self, voice: int) -> None:
        midi_note = int(self.notes["pitch"].get(all=True)[voice])
        self.midi_data_logger.load_note_off_data(voice, midi_note)

        synth_type = self._get_synth_type(midi_note)

        if synth_type == "pianoteq":
            self.server.makenote(midi_note, 0, 0)
            return

        else:
            if synth_type == "transducer":
                synth = self.transducer_synth
            else:
                synth = self.gong_synth

            synth.stop(midi_note)
