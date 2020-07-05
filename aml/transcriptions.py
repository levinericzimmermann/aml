import functools
import math
import operator
import quicktions as fractions
import pathlib
import subprocess

import abjad

import xml.etree.ElementTree as ET

from mu.mel import mel
from mu.mel import ji
from mu.midiplug import midiplug
from mu.sco import old
from mu.rhy import indispensability
from mu.rhy import rhy
from mu.utils import tools

from mutools import bpm_extract
from mutools import lily
from mutools import quantizise

from aml import complex_meters
from aml import globals_


class MeterTranscriber(object):
    def __init__(self):
        self.potential_meters = self._generate_potential_meters()

    def __call__(self, melody: old.Melody) -> tuple:
        return self.estimate_best_meter(melody)

    def estimate_best_meter(self, melody: old.Melody) -> tuple:
        """Return (Melody, TimeSignature) - pair."""
        meter_fitness_pairs = []
        for meter in self.potential_meters:
            n_potential_upbeats = int(
                fractions.Fraction(meter[0].numerator, meter[0].denominator)
                / fractions.Fraction(1, 8)
            )
            for n_upbeats in range(n_potential_upbeats):
                adadpted_melody = melody.copy()
                if n_upbeats:
                    adadpted_melody.insert(
                        0, old.Rest(n_upbeats * fractions.Fraction(1, 8))
                    )
                metricity = self._calculate_metricity_of_melody(meter, adadpted_melody)
                meter_fitness_pairs.append((adadpted_melody, meter[0], metricity))

        return max(meter_fitness_pairs, key=operator.itemgetter(2))[:2]

    @staticmethod
    def _generate_potential_meters() -> tuple:
        """Return tuple filled with subtuples where one subtuple represents one meter.

        Each subtuple is composed of (TIME_SIGNATURE, INDISPENSABILITY_PER_BEAT).
        """
        return tuple(
            (
                abjad.TimeSignature(ts),
                tools.scale(indispensability.indispensability_for_bar(primes), 0, 1),
            )
            for ts, primes in globals_.AVAILABLE_TIME_SIGNATURES
        )

    @staticmethod
    def _calculate_metricity_of_melody(
        time_signature: tuple, melody: old.Melody
    ) -> float:
        duration = melody.duration

        fitness_per_beat = {}
        rising = fractions.Fraction(1, 8)
        position = 0
        for _ in range(
            int(
                math.ceil(
                    duration
                    / (time_signature[0].numerator / time_signature[0].denominator)
                )
            )
        ):
            for fitness in time_signature[1]:
                fitness_per_beat.update({position: fitness})
                position += rising

        metricity = 0
        for tone in melody.convert2absolute():
            if tone.pitch:
                try:
                    metricity += fitness_per_beat[tone.delay]
                except KeyError:
                    metricity -= 0.01

        return metricity


class TimeTranscriber(object):
    r"""Class to convert raw musical data to precise noteable rhythms, metre & tempo."""

    def __init__(
        self,
        n_divisions: int = 8,
        min_tone_size: fractions.Fraction = fractions.Fraction(1, 32),
        min_rest_size: fractions.Fraction = fractions.Fraction(1, 16),
        tempo_estimation_method: str = "librosa",
        stretch_factor: float = fractions.Fraction(1, 8),
        post_stretch_factor: fractions.Fraction = fractions.Fraction(2, 1),
        remove_repeating_pitches: bool = False,
        meter_transcriber: MeterTranscriber = complex_meters.ComplexMeterTranscriber(),
    ):
        self.tempo_estimation_method = tempo_estimation_method
        self.n_divisions = n_divisions
        self.min_tone_size = min_tone_size
        self.min_rest_size = min_rest_size
        self.stretch_factor = stretch_factor
        self.post_stretch_factor = post_stretch_factor
        self.remove_repeating_pitches = remove_repeating_pitches
        self.meter_transcriber = meter_transcriber

    @staticmethod
    def _filter_raw_data_and_convert2melody(raw_data: tuple) -> old.Melody:
        melody = old.Melody([], time_measure="absolute")

        for tone in raw_data:
            pitch, start, stop_time, volume = tone

            if melody:
                stop_last_tone = melody[-1].duration
                difference = start - stop_last_tone

                if difference > 0:
                    melody.append(old.Tone(mel.TheEmptyPitch, stop_last_tone, start))

                elif difference < 0:
                    melody[-1].duration += difference

            else:
                if start != 0:
                    melody.append(old.Tone(mel.TheEmptyPitch, 0, start))

            melody.append(old.Tone(pitch, start, stop_time, volume=volume))

        melody = melody.convert2relative()

        if melody[0].pitch.is_empty:
            melody = melody[1:]

        return melody

    def __eq__(self, other) -> bool:
        try:
            attributes = (
                "tempo_estimation_method",
                "n_divisions",
                "min_tone_size",
                "min_rest_size",
                "stretch_factor",
                "post_stretch_factor",
                "remove_repeating_pitches",
            )
            return all(
                tuple(
                    getattr(self, attr) == getattr(other, attr) for attr in attributes
                )
            )
        except AttributeError:
            return False

    @property
    def json_key(self) -> tuple:
        return tuple(
            getattr(self, attr)
            for attr in (
                "tempo_estimation_method",
                "n_divisions",
                "min_tone_size",
                "min_rest_size",
                "stretch_factor",
                "post_stretch_factor",
                "remove_repeating_pitches",
            )
        )

    def __call__(self, sf_path: str, raw_data: tuple) -> tuple:
        """Return (old.Melody, bars)."""

        # convert raw data to relative - time - based melody
        melody = self._filter_raw_data_and_convert2melody(raw_data)

        # estimate tempo of soundfile
        tempo = self.estimate_tempo(sf_path)

        # divide tempo by 60 and multiply time values with factor to get values where one
        # whole notes equals 1, one halve note equals 0.5, etc.
        factor = tempo / 60
        melody.dur = rhy.Compound(melody.dur).stretch(factor)
        melody.delay = rhy.Compound(melody.delay).stretch(factor)

        # quantizise rhythmical values to precise numbers
        melody = self.estimate_rhythm(melody)

        if self.remove_repeating_pitches:
            melody = melody.tie()

        # detect metre of melody and adjust melody
        melody, metre, spread_metrical_loop = self.estimate_metre(melody)

        return melody, metre, spread_metrical_loop, tempo

    def estimate_tempo(self, sf_path: str, params: dict = None) -> float:
        return bpm_extract.BPM(
            sf_path, method=self.tempo_estimation_method, params=params
        )

    def estimate_rhythm(self, melody: old.Melody) -> tuple:
        melody.dur = rhy.Compound(melody.dur).stretch(self.stretch_factor)
        melody.delay = rhy.Compound(melody.delay).stretch(self.stretch_factor)
        melody = quantizise.quantisize_rhythm(
            melody, self.n_divisions, self.min_tone_size, self.min_rest_size
        )
        melody.dur = rhy.Compound(melody.dur).stretch(self.post_stretch_factor)
        melody.delay = rhy.Compound(melody.delay).stretch(self.post_stretch_factor)
        return melody

    def estimate_metre(self, melody: old.Melody) -> tuple:
        return self.meter_transcriber(melody)


class ComplexScaleTranscriber(object):
    r"""Class to quantizise a series of frequencies with a complex scale.

    A complex scale is defined as a scale that has multiple options or intonations for the
    same scale degree.
    """

    def __init__(self, original_scale: tuple, intonations_per_scale_degree: tuple):
        self._scale_size = len(original_scale)
        self._original_scale = original_scale
        self._intonations_per_scale_degree = intonations_per_scale_degree
        dtosdpsd = self.find_distance_to_other_scale_degrees_per_scale_degree(
            original_scale
        )
        self._distance_to_other_scale_degrees_per_scale_degree = dtosdpsd
        self._deviation_from_ideal_scale_degree_per_intonation = tuple(
            tuple(intonation.cents - ideal for intonation in scale_degree)
            for scale_degree, ideal in zip(intonations_per_scale_degree, original_scale)
        )

    @staticmethod
    def find_distance_to_other_scale_degrees_per_scale_degree(
        original_scale: tuple
    ) -> tuple:
        distance_to_other_scale_degrees_per_scale_degree = []

        for scale_degree0 in original_scale:
            distance_to_other_scale_degrees = []
            for octave in (-1, 0, 1):
                for scale_degree1_idx, scale_degree1 in enumerate(original_scale):
                    scale_degree1 += 1200 * octave
                    difference = scale_degree1 - scale_degree0
                    distance_to_other_scale_degrees.append(
                        ((scale_degree1_idx, octave), difference)
                    )

            distance_to_other_scale_degrees_per_scale_degree.append(
                tuple(distance_to_other_scale_degrees)
            )

        return tuple(distance_to_other_scale_degrees_per_scale_degree)

    def _detect_starting_scale_degree(self, cent_distances: tuple) -> int:
        scale_degree_fitness_pairs = []

        for scale_degree in range(self._scale_size):
            fitness = 0

            last_scale_degree = int(scale_degree)
            for distance in cent_distances:

                closest_item = tools.find_closest_item(
                    distance,
                    self._distance_to_other_scale_degrees_per_scale_degree[
                        last_scale_degree
                    ],
                    key=operator.itemgetter(1),
                )

                fitness += abs(distance - closest_item[1])
                last_scale_degree = closest_item[0][0]

            scale_degree_fitness_pairs.append((scale_degree, fitness))

        return min(scale_degree_fitness_pairs, key=operator.itemgetter(1))[0]

    def _make_transcription(
        self,
        starting_scale_degree: int,
        starting_intonation: int,
        cent_distances: float,
    ) -> tuple:

        pitches = [(starting_scale_degree, starting_intonation, 0)]
        fitness = 0

        for distance in cent_distances:
            last_scale_degree, last_intonation, last_octave = pitches[-1]
            adapted_distance = (
                distance
                + self._deviation_from_ideal_scale_degree_per_intonation[
                    last_scale_degree
                ][last_intonation]
            )
            closest_item = tools.find_closest_item(
                adapted_distance,
                self._distance_to_other_scale_degrees_per_scale_degree[
                    last_scale_degree
                ],
                key=operator.itemgetter(1),
            )

            new_scale_degree = closest_item[0][0]
            new_octave = last_octave + closest_item[0][1]

            last_pitch = self._intonations_per_scale_degree[last_scale_degree][
                last_intonation
            ]
            last_pitch += ji.r(1, 1).register(last_octave)

            octavater = ji.r(1, 1).register(new_octave)
            possible_intonations = tuple(
                intonation + octavater
                for intonation in self._intonations_per_scale_degree[new_scale_degree]
            )
            last_pitch_cents = last_pitch.cents
            distance_per_intonation = tuple(
                into.cents - last_pitch_cents for into in possible_intonations
            )
            new_intonation = tools.find_closest_index(distance, distance_per_intonation)

            pitches.append((new_scale_degree, new_intonation, new_octave))
            fitness += distance_per_intonation[new_intonation]

        return tuple(pitches), fitness

    def __call__(self, frequencies: tuple) -> tuple:
        cent_distances = tuple(
            mel.SimplePitch.hz2ct(f0, f1)
            for f0, f1 in zip(frequencies, frequencies[1:])
        )
        starting_scale_degree = self._detect_starting_scale_degree(cent_distances)

        transcription_and_fitness_pairs = []
        for n, intonation in enumerate(
            self._intonations_per_scale_degree[starting_scale_degree]
        ):
            transcription_and_fitness_pairs.append(
                self._make_transcription(starting_scale_degree, n, cent_distances)
            )

        best = min(transcription_and_fitness_pairs, key=operator.itemgetter(1))[0]

        # convert abstract data to actual pitch objects
        return tuple(
            self._intonations_per_scale_degree[data[0]][data[1]]
            + ji.r(1, 1).register(data[2])
            for data in best
        )


class Transcription(old.Melody):
    r"""Class for the transcription of monophonic melodies.

    First melodies have to be analysed with the software Tony. Then the results have to
    be saved in the SVL format. Those files can be further analysed and transformed
    using this Transcription class.
    """

    _tmp_name = "{}/../../tmp/qiroah_transcription".format(pathlib.Path.home())

    def __init__(
        self,
        melody: tuple,
        bars: tuple = None,
        frequency_range: tuple = None,
        ratio2pitchclass_dict: dict = None,
        tempo: float = None,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop = None,
        concert_pitch: float = None,
    ):
        self.__bars = bars
        self.__tempo = tempo
        self.__frequency_range = frequency_range
        self.__ratio2pitchclass_dict = ratio2pitchclass_dict
        self.__concert_pitch = concert_pitch
        self.__spread_metrical_loop = spread_metrical_loop
        super().__init__(melody)

    @property
    def spread_metrical_loop(self) -> complex_meters.SpreadMetricalLoop:
        return self.__spread_metrical_loop

    def copy(self) -> "Transcription":
        return type(self)(
            self,
            self.bars,
            self.frequency_range,
            self.ratio2pitchclass_dict,
            self.tempo,
            self.concert_pitch,
        )

    @property
    def bars(self) -> tuple:
        return self.__bars

    @property
    def ratio2pitchclass_dict(self) -> tuple:
        return self.__ratio2pitchclass_dict

    @property
    def tones(self) -> tuple:
        return self.__tones

    @property
    def tempo(self) -> tuple:
        return self.__tempo

    @property
    def concert_pitch(self) -> float:
        if self.__concert_pitch:
            return self.__concert_pitch
        else:
            return 261.626

    @property
    def frequency_range(self) -> tuple:
        return self.__frequency_range

    @staticmethod
    def _get_root(path: str):
        tree = ET.parse(path)
        return tree.getroot()

    @staticmethod
    def _filter_data_from_root(root) -> tuple:
        data = []
        sr = int(root[0][0].attrib["sampleRate"])
        for child in root[0][1]:
            start = int(child.attrib["frame"]) / sr
            duration = int(child.attrib["duration"]) / sr
            freq = float(child.attrib["value"])
            volume = float(child.attrib["level"])
            stop_time = start + duration

            data.append([freq, start, stop_time, volume])

        return tuple(map(tuple, data))

    @classmethod
    def from_complex_scale(
        cls,
        svl_path: str,
        sf_path: str,
        complex_scale_transcriber: ComplexScaleTranscriber,
        time_transcriber: TimeTranscriber,
        octave_of_first_pitch: int = 0,
        ratio2pitchclass_dict: dict = None,
    ) -> "Transcription":
        root = cls._get_root(svl_path)
        frequency_range = root[0][0].attrib["minimum"], root[0][0].attrib["maximum"]
        data = cls._filter_data_from_root(root)

        frequencies = tuple(map(operator.itemgetter(0), data))
        octavater = ji.r(1, 1).register(octave_of_first_pitch)
        pitches = tuple(
            octavater + pitch for pitch in complex_scale_transcriber(frequencies)
        )
        new_data = tuple((pitch,) + tone[1:] for pitch, tone in zip(pitches, data))

        melody, metre, spread_metrical_loop, tempo = time_transcriber(sf_path, new_data)
        if isinstance(metre, abjad.TimeSignature):
            bars = tuple(
                metre
                for i in range(
                    int(
                        math.ceil(
                            melody.duration
                            / fractions.Fraction(metre.numerator, metre.denominator)
                        )
                    )
                )
            )
        else:
            bars = metre
        return cls(
            melody,
            bars,
            frequency_range,
            ratio2pitchclass_dict,
            float(tempo),
            spread_metrical_loop,
        )

    def show(self, reference_pitch: int = 0) -> None:
        self.notate(self._tmp_name, reference_pitch)
        subprocess.call(["o", "{}.png".format(self._tmp_name)])

    def play(self) -> None:
        self.synthesize(self._tmp_name)
        subprocess.call(["o", "{}.wav".format(self._tmp_name)])

    def notate(self, name: str) -> None:
        pitches, delays = self.pitch, self.delay

        bar_grid = tuple(
            fractions.Fraction(ts.numerator, ts.denominator) for ts in self.bars
        )
        grid = tuple(
            fractions.Fraction(1, 4)
            for i in range(int(math.ceil(self.duration / fractions.Fraction(1, 4))))
        )

        notes = abjad.Voice([])

        absolute_delay = tools.accumulate_from_zero(delays)
        for pitch, delay, start, stop in zip(
            pitches, delays, absolute_delay, absolute_delay[1:]
        ):
            seperated_by_bar = tools.accumulate_from_n(
                lily.seperate_by_grid(start, stop, bar_grid, hard_cut=True), start
            )
            sub_delays = functools.reduce(
                operator.add,
                tuple(
                    functools.reduce(
                        operator.add,
                        tuple(
                            lily.seperate_by_assignability(d)
                            for d in lily.seperate_by_grid(start, stop, grid)
                        ),
                    )
                    for start, stop in zip(seperated_by_bar, seperated_by_bar[1:])
                ),
            )
            subnotes = []
            if pitch.is_empty:
                ct = None
            else:
                if self.ratio2pitchclass_dict:
                    ct = lily.convert2abjad_pitch(pitch, self.ratio2pitchclass_dict)

                else:
                    ct = lily.round_cents_to_12th_tone(pitch.cents)

            for delay in sub_delays:
                if ct is None:
                    obj = abjad.Rest(delay)
                else:
                    obj = abjad.Note(ct, delay)

                subnotes.append(obj)

            if ct is not None and len(subnotes) > 1:
                for note in subnotes[:-1]:
                    abjad.attach(abjad.Tie(), note)

            notes.extend(subnotes)

        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"), notes[0]
        )
        abjad.attach(self.bars[0], notes[0], context="Voice")

        score = abjad.Score([notes])

        lf = abjad.LilyPondFile(
            score,
            lilypond_version_token=abjad.LilyPondVersionToken("2.19.83"),
            includes=["lilypond-book-preamble.ly"],
        )

        lily_name = "{}.ly".format(name)

        with open(lily_name, "w") as f:
            f.write(lily.EKMELILY_PREAMBLE)
            f.write(format(lf))

        subprocess.call(["lilypond", "--png", "-dresolution=400", lily_name])

    def synthesize(self, name: str) -> None:
        sequence = []
        for tone in self:
            p = tone.pitch
            d = tone.delay
            p.multiply = self.concert_pitch
            d *= 4
            sequence.append(midiplug.PyteqTone(p, d, d))

        midiplug.Pianoteq(sequence).export2wav(name, preset='"Erard Player"')


class QiroahTranscription(Transcription):
    @classmethod
    def from_complex_scale(
        cls,
        chapter: int = 59,
        verse: str = "opening",
        time_transcriber=TimeTranscriber(),
        octave_of_first_pitch: int = 0,
        use_full_scale: bool = False,
    ) -> "QiroahTranscription":
        svl_path = "aml/transcriptions/qiroah_{}_{}.svl".format(chapter, verse)
        sf_path = "aml/samples/qiroah/without_reverb/qiroah_{}_{}.wav".format(
            chapter, verse
        )

        if use_full_scale:
            complex_scale_transcriber = ComplexScaleTranscriber(
                globals_.ORIGINAL_SCALE, globals_.INTONATIONS_PER_SCALE_DEGREE
            )
        else:
            complex_scale_transcriber = ComplexScaleTranscriber(
                globals_.FILTERED_ORIGINAL_SCALE,
                globals_.FILTERED_INTONATIONS_PER_SCALE_DEGREE,
            )

        return super(QiroahTranscription, cls).from_complex_scale(
            svl_path,
            sf_path,
            complex_scale_transcriber,
            time_transcriber,
            octave_of_first_pitch=octave_of_first_pitch,
            ratio2pitchclass_dict=globals_.RATIO2PITCHCLASS,
        )
