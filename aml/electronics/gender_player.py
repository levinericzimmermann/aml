"""This file implements the live-electronic module for triggering processed gender samples."""

import collections
import json
import os

import pyo

import yamm

from mu.mel import ji
from mu.utils import infit

import midi
import modules
import spat


class GenderGenerator(pyo.TableRead, metaclass=midi._GongSamplerMetaClass):
    _path = "samples/gender/adapted"
    pitch_per_idx = tuple(ji.JIMel.load_json("{}/idx2pitch.json".format(_path)))
    _start_at_cycle = infit.Cycle(range(3))
    _is_inverse_cycle = infit.Cycle((False, True))

    def __init__(self):
        self.fader = pyo.Fader(fadein=0.001, fadeout=0.1)
        super().__init__(self.snd_tables[0][0], mul=self.fader)

        self._left_right_cycle_per_sample = [
            infit.ActivityLevel(
                5,
                start_at=next(self._start_at_cycle),
                is_inverse=next(self._is_inverse_cycle),
            )
            for _ in self.snd_tables
        ]

    def get_nth_snd_table(self, idx: int):
        return self.snd_tables[idx][next(self._left_right_cycle_per_sample[idx])]

    def play(self, pitch: ji.JIPitch, fadeout_time: float, *args, **kwargs):
        new_table = self.get_nth_snd_table(self.pitch_per_idx.index(pitch))

        duration = new_table.getDur()
        fader_duration = duration * fadeout_time
        fadeout_time = 0.1
        if fadeout_time > fader_duration:
            fadeout_time = fader_duration * 0.9
        self.fader.setDur(fader_duration)
        self.fader.setFadeout(fadeout_time)
        self.fader.play()

        self.setTable(new_table)
        self.setFreq(new_table.getRate())
        return super().play(*args, **kwargs)


class GenderPlayer(modules.Module):
    name = "gender_sample_player"
    _stochastic_analysis_path = "../stochastic_pitch_analysis"

    def __init__(
        self,
        strings: tuple,
        midi_synth: midi.MidiSynth,
        spat_maker: spat.BalancedSpatMaker,
        n_voices: int = 4,
    ):
        super().__init__()
        self._mixer = pyo.Mixer(outs=4, chnls=1, time=0.025)

        self._markov_chains = self._make_markov_chains()

        self._midi_synth = midi_synth
        self.strings = strings
        self._generators = [GenderGenerator() for _ in range(n_voices)]
        self._generator_idx_cycle = infit.Cycle(range(n_voices))
        self._spatialised_generators = [
            spat_maker.make_spatialised_signal(gen, n_voices=4)
            for gen in self._generators
        ]
        self._summed_generators = sum(self._spatialised_generators)
        self._previous_played_pitches = collections.deque([], maxlen=15)

        self._trig_func = pyo.TrigFunc(
            tuple(self.strings.values())[0].attack_detector, self.trigger_events
        )
        self._trig_func.stop()

        self._add_summed_generators_to_mixer()

    def _add_summed_generators_to_mixer(self) -> None:
        for n in range(4):
            self._mixer.addInput(n, self._summed_generators[n])
            self._mixer.setAmp(n, n, 1)

    @staticmethod
    def _load_stochastic_analysis(path: str) -> dict:
        with open(path, "r") as f:
            raw_data = json.load(f)

        analysis = {
            ji.r(*p0): {ji.r(*p1): likelihood for p1, likelihood in subdata}
            for p0, subdata in raw_data
        }
        return analysis

    @staticmethod
    def _combine_multiple_stochastic_analysis(*analysis: dict) -> dict:
        combined_analysis = analysis[0]
        for nth, an in enumerate(analysis[1:]):
            for pitch, stochastic_data in an.items():
                for pitch1, likelihood in stochastic_data.items():
                    combined_analysis[pitch][pitch1] = (
                        (combined_analysis[pitch][pitch1] * (nth + 1)) + likelihood
                    ) / (nth + 2)

        return combined_analysis

    def _make_markov_chains(self) -> tuple:
        stochastic_pitch_analysis = self._combine_multiple_stochastic_analysis(
            *tuple(
                self._load_stochastic_analysis(
                    "{}/{}".format(self._stochastic_analysis_path, f)
                )
                for f in os.listdir(self._stochastic_analysis_path)
            )
        )

        chain_with_pitch_repetitions = yamm.Chain(
            {
                (p,): stochastic_data
                for p, stochastic_data in stochastic_pitch_analysis.items()
            }
        )
        chain_without_pitch_repetitions = yamm.Chain(
            {
                (p,): {
                    p1: likelihood
                    for p1, likelihood in stochastic_data.items()
                    if p1 != p
                }
                for p, stochastic_data in stochastic_pitch_analysis.items()
            }
        )
        return chain_with_pitch_repetitions, chain_without_pitch_repetitions

    @property
    def mixer(self) -> pyo.Mixer:
        return self._mixer

    @property
    def pitch_stack(self) -> midi.PitchStack:
        return self._midi_synth.pitch_stack

    def trigger_events(self) -> None:
        n_events_to_trigger = next(self.n_attackes_per_trigger_maker)

        wait = 0
        for _ in range(n_events_to_trigger):
            wait += self.trigger_event(wait)

    def _find_pitch(self) -> ji.JIPitch:
        # detect all potential pitches
        pp = self.pitch_stack.get_all_pitches_that_appeared_within_the_last_n_seconds(
            self.find_pitches_within_the_last_n_seconds
        )
        if pp:
            reference_pitch = pp[0]
            normalized_pitch = reference_pitch.normalize()
            choosen_pitch = self._markov_chains[1].walk_until((normalized_pitch,), 2)[1]
            return choosen_pitch

    def trigger_event(self, wait: float = 0) -> float:
        # (0) find pitch
        # (1) (find used sample index) => thats done within the generator
        # (2) find waiting time
        # (3) get sound generator
        # (4) spatialise
        # (5) play
        # (6) return waiting time
        pitch = self._find_pitch()
        if pitch:
            responsible_sound_generator_idx = next(self._generator_idx_cycle)
            self._spatialised_generators[responsible_sound_generator_idx].update()
            self._generators[responsible_sound_generator_idx].play(
                pitch, next(self.fadeout_maker), delay=wait
            )
            self._spatialised_generators[responsible_sound_generator_idx].play(
                delay=wait
            )
        return wait

    def _play(
        self,
        tempo: float = 40,
        rhythm_cycle: infit.InfIt = infit.Cycle((0,)),
        n_attackes_per_trigger_maker: infit.InfIt = infit.Cycle((1,)),
        allowed_register: tuple = (-1, 0, 1),
        allowed_soundgenerator: tuple = ("gender",),
        fadeout_maker: infit.InfIt = infit.Cycle((1,)),
        amp_maker: infit.InfIt = infit.Uniform(0.5, 1),
        find_pitches_within_the_last_n_seconds: float = 3,
        instruments_to_analyse: tuple = ("violin", "viola", "cello"),
        # onset detector arguments
        deltime: float = 0.005,
        cutoff: float = 70,
        maxthresh: float = 3,
        minthresh: float = -20,
        reltime: float = 0.15,
    ):
        self._stop()

        # override previous attributes
        self.rhythm_cycle = rhythm_cycle
        self.n_attackes_per_trigger_maker = n_attackes_per_trigger_maker
        self.allowed_register = allowed_register
        self.allowed_soundgenerator = allowed_soundgenerator
        self.fadeout_maker = fadeout_maker
        self.amp_maker = amp_maker
        self.find_pitches_within_the_last_n_seconds = (
            find_pitches_within_the_last_n_seconds
        )

        # configure & collect onset detector
        trigger_signals = []
        for string_name, string_object in self.strings.items():
            if string_name in instruments_to_analyse:
                string_object.attack_detector.deltime = deltime
                string_object.attack_detector.cutoff = cutoff
                string_object.attack_detector.maxthresh = maxthresh
                string_object.attack_detector.minthresh = minthresh
                string_object.attack_detector.play()
                trigger_signals.append(string_object.attack_detector)

        # start function for triggering new samples
        self._trig_func.input = trigger_signals
        self._trig_func.play()

    def _stop(self):
        for string in self.strings.values():
            string.attack_detector.stop()

        self._trig_func.stop()
