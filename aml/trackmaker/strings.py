"""Simple sampler for generating simulations of string instruments.

It uses the open-source VSCO-2 sample package.

The expected sample paths are
    .local/share/sounds/Solo_Contrabass
    .local/share/sounds/Solo_Violin
"""

import abc
import numpy as np
import itertools
import operator
import os
import json
import random

import quicktions as fractions

import abjad

import samplyser

from mu.mel import mel
from mu.mel import ji
from mu.midiplug import midiplug
from mu.sco import old
from mu.utils import infit
from mu.utils import tools

from mutools import attachments
from mutools import mus
from mutools import lily
from mutools import synthesis

from aml import complex_meters
from aml import comprovisation
from aml import globals_


####################################################################################
#                            defining TrackClass                                   #
####################################################################################


class String(mus.Track):
    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        resolution: int = None,
    ):

        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"),
            abjad_data[0][0][0],
        )
        abjad_data[2].lilypond_type = "RhythmicStaff"
        for orientation_staff in (abjad_data[0], abjad_data[2]):
            abjad.attach(
                abjad.LilyPondLiteral("\\magnifyStaff #4/7", "before"),
                orientation_staff[0][0],
            )

        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic-first", "before"),
            abjad_data[1][0][0],
        )
        super().__init__(abjad_data, sound_engine, resolution)


####################################################################################
#                           defining different sound engines                       #
####################################################################################


class Sample(object):
    def __init__(self, path: str, freq: float, dynamic: float, playing_technique: str):
        self._path = path
        self._freq = freq
        self._dynamic = dynamic
        self._playing_technique = playing_technique

    @property
    def path(self) -> str:
        return self._path

    @property
    def freq(self) -> float:
        return self._freq

    @property
    def dynamic(self) -> int:
        return self._dynamic

    @property
    def playing_technique(self) -> int:
        return self._playing_technique

    def __repr__(self) -> str:
        return "Sample({}, {}, {})".format(
            self._freq, self._dynamic, self._playing_technique
        )


def _make_samples(sample_paths: tuple) -> tuple:
    samples = []

    pitch_analyser = samplyser.Analyser(samplyser.pitch.detector.freq_from_hps)
    for instrument_path in sample_paths:
        for playing_technique in os.listdir(instrument_path):
            instrument_and_playing_technique_path = "{}/{}".format(
                instrument_path, playing_technique
            )
            files = os.listdir(instrument_and_playing_technique_path)
            for sample in files:
                if sample[-3:] == "wav":
                    sample_name_without_path = sample[:-4]
                    sample_json_name = "{}.json".format(sample_name_without_path)

                    complete_sample_path = "{}/{}".format(
                        instrument_and_playing_technique_path, sample
                    )
                    complete_sample_json_path = "{}/{}".format(
                        instrument_and_playing_technique_path, sample_json_name
                    )

                    if sample_json_name not in files:
                        if "pizz" in sample.lower():
                            split_sample_name = sample.split("_")
                            pitch_name = split_sample_name[2].lower()
                            frequency = abjad.NamedPitch(pitch_name).hertz
                            with open(complete_sample_json_path, "w") as f:
                                json.dump({complete_sample_path: [frequency]}, f)

                        else:
                            pitch_analyser(complete_sample_path, output=True)

                    frequency = json.load(open(complete_sample_json_path, "r"))[
                        complete_sample_path
                    ][0]

                    try:
                        dynamic = sample.split("_")[3]
                        if dynamic in ("p", "v1"):
                            dynamic = 0
                        else:
                            dynamic = 1
                    except IndexError:
                        dynamic = 0

                    samples.append(
                        Sample(
                            complete_sample_path,
                            frequency,
                            dynamic,
                            playing_technique.lower(),
                        )
                    )

    return tuple(samples)


class SampleBasedStringSoundEngine(synthesis.BasedCsoundEngine):
    _samples = _make_samples(
        tuple(
            "{}/{}".format(os.path.expanduser("~"), path)
            for path in (
                ".local/share/sounds/Solo_Contrabass",
                ".local/share/sounds/Solo_Violin",
                # ".local/share/sounds/Cello_Section",
                # ".local/share/sounds/Viola_Section",
            )
        )
    )

    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )

    @property
    def cname(self) -> str:
        return ".string_sampler"

    @property
    def orc(self) -> str:
        # wie werden die samples bearbeitet?
        #   0. sample wird nach einlesen direkt zu einem monosignal zusammen gemischt
        #   1. tonhöhe wird mithilfe von linseg gemacht: die glissando points werden erst
        #   analysiert (vibrato wird nicht beachtet) und beschrieben und dann in csound
        #   linseg
        #   übersetzt.
        #   2. sample wird normalisiert und dann mit der eingangslautstärke multipliziert.
        #   3. sample wird zum schluss ausgefaded (linseg mit duration)
        #   4. falls sample nicht lange genug ist und spieltechnik es zu lässt, wird das
        #   gleiche sample mehrmals geloopt, bis das ende erreicht ist.

        n_channels = 2
        channel2use = tuple(range(n_channels))

        name_of_signals = tuple("aSignal{}".format(idx) for idx in range(n_channels))

        volseg = "kvol linseg 0, 0.1, 1, p3 - 0.2, 1, 0.1, 0"
        diskin2 = "{} diskin2 p4, p5, 0, 0, 6, 4".format(", ".join(name_of_signals))
        summarized = " + ".join(
            tuple(
                signal
                for sig_idx, signal in enumerate(name_of_signals)
                if sig_idx in channel2use
            )
        )
        summarized = "aSummarized = ({}) / {}".format(summarized, len(channel2use))
        sig = "asig = aSummarized * kvol * p6"
        out = "out asig"

        lines = (
            "0dbfs=1",
            "gisine  ftgen	0,0,4096,10,1",
            "gaSendL, gaSendR init 0",
            "nchnls=1",
            "instr 1",
            volseg,
            diskin2,
            summarized,
            sig,
            "gaSendL  =        gaSendL + asig/3",
            "gaSendR  =        gaSendR + asig/3",
            out,
            "endin",
            "instr 2",
            "aRvbL,aRvbR reverbsc gaSendL,gaSendR,0.9,7000",
            "out     (aRvbL + aRvbR) * 0.385",
            "clear    gaSendL,gaSendR",
            "endin",
        )

        return "\n".join(lines)

    @property
    def sco(self) -> str:
        lines = ["i2 0 {}".format(float(self._novent_line.duration))]
        for novent_abs, novent in zip(
            self._novent_line.convert2absolute(), self._novent_line
        ):
            samples = self.find_samples(novent)
            delay, duration = float(novent_abs.delay), float(novent.duration)
            volume = novent.volume
            if not volume:
                volume = 1
            else:
                volume = float(volume)

            for sample, expected_freq in samples:
                pitch_factor = expected_freq / sample.freq
                line = 'i1 {} {} "{}" {} {}'.format(
                    delay, duration, os.path.relpath(sample.path), pitch_factor, volume
                )
                lines.append(line)

        return "\n".join(lines)

    def find_samples(self, novent: lily.NOvent) -> tuple:
        # dynamik wird zuerst über lautstärke des ursprungssamples festgestellt: v1 -> p,
        # vANYTHING -> f, oder p -> p und f -> f. dann wird das passendere sample genommen
        # und
        # normalisiert und dann auf entsprechende lautstärke multipliziert.

        # wie wird sich für ein sample entschieden?
        #   1. nach spieltechniken sortieren (falls kein sample mit der spieltechnik gibt,
        #   log
        #   warning, aber benutze dann einfach alle samples
        #   2. nach tonhöhe in der nähe sortieren. alle tonhöhen die innerhalb von 75 ct
        #   liegen können benutzt werden
        #   3. nach dynamik sortieren: wie viele level gibt es zur auswahl und was ist die
        #   gegenwärtige dynamik? dann alle diejenigen samples rausfiltern, deren dynamik
        #   am
        #   nächsten ist (wenn nur 0 und 1 gibt: für dynamik 0.4 -> die erste lautstärke
        #   benutzen, für dynamik 0.7 -> die zweite lautstärke benutzen)
        #   4. davon einfach das erste nehmen

        allowed_dynamic = (0,)

        if novent.tremolo:
            pt = ("trem",)

        elif novent.string_contact_point == attachments.StringContactPoint("pizzicato"):
            pt = ("pizz",)
            allowed_dynamic = (1,)

        elif novent.articulation_once == attachments.ArticulationOnce("."):
            pt = ("spic",)

        elif novent.articulation == attachments.Articulation("."):
            pt = ("spic",)

        else:
            pt = ("susvib", "arcovib")

        allowed_samples = tuple(
            sorted(
                tuple(
                    s
                    for s in self.samples
                    if s.playing_technique in pt and s.dynamic in allowed_dynamic
                ),
                key=lambda s: s.freq,
            )
        )
        frequencies = tuple(float(s.freq) for s in allowed_samples)

        samples = []
        for pitch in novent.pitch:
            f = float(pitch) * globals_.CONCERT_PITCH
            samples.append(
                (allowed_samples[tools.find_closest_index(f, frequencies)], f)
            )

        return tuple(samples)

    @property
    def samples(self) -> tuple:
        return self._samples


class PMStringSoundEngine(synthesis.BasedCsoundEngine):
    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )

    @property
    def cname(self) -> str:
        return ".string_pm"

    @property
    def orc(self) -> str:
        randpressure = "kpres rspline 1.5, 4, 0.5, 2"
        randlp = "klpfreq rspline 2000, 3400, 1, 3.8"
        randrat = "krat rspline 0, 0.005, 0.4, 1.8"
        randvol = "kvol rspline 0.6, 1, 3, 5"
        randvib = "kvib rspline 2, 8, 0.8, 4"
        linseg = "klinvol linseg 0, 0.1, 1, p3 - 0.2, 1, 0.1, 0"
        signal = "asig  wgbow p5, p4, p6 + kpres, p7 + krat, kvib, p9, gisine"
        filter0 = "asig butlp asig, klpfreq"
        filter1 = "asig pareq asig, 80, 6, 0.707"
        out = "out asig"
        lines = (
            "0dbfs=1.95",
            "gisine  ftgen	0,0,4096,10,1",
            "gaSendL,gaSendR init 0",
            "nchnls=1",
            "instr 1",
            randlp,
            linseg,
            randrat,
            randvol,
            randvib,
            randpressure,
            signal,
            filter0,
            filter1,
            "asig = asig * kvol * klinvol",
            "gaSendL  =        gaSendL + asig/3",
            "gaSendR  =        gaSendR + asig/3",
            out,
            "endin",
            "instr 2",
            "aRvbL,aRvbR reverbsc gaSendL,gaSendR,0.9,7000",
            "out     (aRvbL + aRvbR) * 0.35",
            "clear    gaSendL,gaSendR",
            "endin",
        )
        return "\n".join(lines)

    @property
    def sco(self) -> str:
        lines = []
        for novent_abs, novent in zip(
            self._novent_line.convert2absolute(), self._novent_line
        ):
            delay, duration = float(novent_abs.delay), float(novent.duration)
            volume = novent.volume
            if not volume:
                volume = 1
            else:
                volume = float(volume)

            for pitch in novent.pitch:
                freq = float(pitch) * globals_.CONCERT_PITCH
                line = "i1 {} {} {} {} {} {} {} {}".format(
                    delay,
                    duration,
                    freq,
                    volume,
                    random.uniform(0, 1.1),
                    random.uniform(0.07, 0.13),
                    random.uniform(0, 1.4),
                    random.uniform(0.0004, 0.003),
                )
                lines.append(line)

        lines.append("i2 0 {}".format(float(self._novent_line.duration)))

        return "\n".join(lines)


class MidiStringSoundEngine(synthesis.SoundEngine):
    CONCERT_PITCH = globals_.CONCERT_PITCH * 0.5

    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )

    def render(self, name: str) -> None:
        """Generate WAV file with input name."""
        seq = []
        for chord in self._novent_line:
            dur = float(chord.delay)
            if chord.pitch != mel.TheEmptyPitch and bool(chord.pitch):
                size = len(chord.pitch)
                for idx, pi in enumerate(chord.pitch):
                    if idx + 1 == size:
                        de = float(dur)
                    else:
                        de = 0
                    if pi != mel.TheEmptyPitch:
                        tone = old.Tone(
                            ji.JIPitch(pi, multiply=self.CONCERT_PITCH),
                            de,
                            dur,
                            volume=chord.volume,
                        )
                    else:
                        tone = old.Tone(mel.TheEmptyPitch, de, dur, volume=chord.volume)
                    seq.append(tone)
            else:
                seq.append(old.Rest(dur))

        mf = midiplug.SimpleMidiFile(seq)
        mf.export("{}.mid".format(name))


class SineStringSoundEngine(synthesis.SineMelodyEngine):
    def __init__(self, novent_line: lily.NOventLine):
        novent_line = comprovisation.process_comprovisation_attachments(novent_line)
        melody = old.Melody(
            [
                old.Tone(
                    ji.JIPitch(novent.pitch[0], multiply=globals_.CONCERT_PITCH),
                    delay=novent.delay,
                    duration=novent.duration,
                )
                if novent.pitch
                else old.Tone(mel.TheEmptyPitch, delay=novent.delay)
                for novent in novent_line
            ]
        )
        super().__init__(melody)


# STRING_SOUND_ENGINE = PMStringSoundEngine
STRING_SOUND_ENGINE = SampleBasedStringSoundEngine
# STRING_SOUND_ENGINE = MidiStringSoundEngine
# STRING_SOUND_ENGINE = SineStringSoundEngine


####################################################################################
#               defining StringMaker - classes and helper classes                  #
####################################################################################


class StringMaker(mus.TrackMaker):
    def __init__(self, instrument: abjad.Instrument) -> None:
        self.instrument = instrument

    def attach_pitches_to_novent(self, pitches: tuple, novent: lily.NOvent) -> None:
        for p in pitches:
            assert p in self.instrument.available_pitches

        novent.pitch = pitches

        if pitches[0] in self.instrument.harmonic_pitches:
            abjad_pitch = lily.convert2abjad_pitch(
                pitches[0] - ji.r(4, 1), globals_.RATIO2PITCHCLASS
            )
            (
                added_pitch_class,
                octave_change,
            ) = globals_.RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE[
                pitches[0].normalize()
            ]
            added_pitch = abjad.NamedPitch(
                abjad.NamedPitchClass(added_pitch_class),
                octave=int(abjad_pitch.octave) + octave_change,
            )
            novent.artifical_harmonic = attachments.ArtificalHarmonicAddedPitch(
                abjad.PitchSegment((abjad_pitch, added_pitch))
            )

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return STRING_SOUND_ENGINE(
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[1])
        )

    def _prepare_staves(
        self, nline: lily.NOventLine, segment_maker: mus.SegmentMaker
    ) -> old.PolyLine:
        polyline = [
            segment_maker.melodic_orientation,
            nline,
            segment_maker.rhythmic_orientation,
        ]

        # add crucial notation elements
        polyline[1][0].clef = attachments.Clef(
            {"cello": "bass", "viola": "alto", "violin": "treble"}[self.instrument.name]
        )
        polyline[1][0].margin_markup = attachments.MarginMarkup(
            "{}.{}".format(segment_maker.chapter, segment_maker.verse)
        )

        for nol in polyline:
            nol[0].tempo = attachments.Tempo((1, 4), segment_maker.tempo)

        return old.PolyLine(polyline)


class SilentStringMaker(StringMaker):
    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        dur = segment_maker.duration
        nline = lily.NOventLine([lily.NOvent(duration=dur, delay=dur)])
        return self._prepare_staves(nline, segment_maker)

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return synthesis.SilenceEngine(1)


class HarmonicPitchArea(object):
    """Helper class for the generation of musical data from harmonic pitches."""

    def __init__(
        self,
        pitch: ji.JIPitch,
        start: fractions.Fraction,
        stop: fractions.Fraction,
        slice_start: fractions.Fraction,
        slice_stop: fractions.Fraction,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
    ):
        self.start = start
        self.stop = stop
        self._slice_start = slice_start
        self._slice_stop = slice_stop
        self._instrument = globals_.PITCH2INSTRUMENT[pitch.normalize()]
        self._pitch = pitch
        self._spread_metrical_loop = spread_metrical_loop

    def __repr__(self) -> str:
        return "HarmonicPitchArea({}, ({}, {}), ({}, {}))".format(
            self.pitch, self.start, self.slice_start, self.stop, self.slice_stop
        )

    @property
    def pitch(self) -> ji.JIPitch:
        return self._pitch

    @property
    def instrument(self) -> str:
        return self._instrument

    @property
    def slice_start(self) -> fractions.Fraction:
        return self._slice_start

    @property
    def slice_stop(self) -> fractions.Fraction:
        return self._slice_stop

    @property
    def potential_duration(self) -> fractions.Fraction:
        return self.stop - self.start

    @property
    def positions(self) -> tuple:
        return self._spread_metrical_loop.get_rhythm_metricity_pairs_for_instrument(
            self.instrument, self.start, self.stop
        )


class StringNOventAdapter(abc.ABC):
    eigenzeit = None

    @abc.abstractmethod
    def __call__(self, novent: lily.NOvent) -> None:
        raise NotImplementedError()


class ArcoAdapter(StringNOventAdapter):
    def __call__(self, novent: lily.NOvent) -> None:
        novent.string_contact_point = attachments.StringContactPoint("ordinario")


class StaccatoAdapter(StringNOventAdapter):
    eigenzeit = fractions.Fraction(1, 8)

    def __call__(self, novent: lily.NOvent) -> None:
        novent.string_contact_point = attachments.StringContactPoint("ordinario")
        novent.articulation_once = attachments.ArticulationOnce(".")


class TremoloAdapter(StringNOventAdapter):
    def __call__(self, novent: lily.NOvent) -> None:
        novent.tremolo = attachments.Tremolo()
        novent.string_contact_point = attachments.StringContactPoint("ordinario")
        novent.volume *= 0.5


class PizzAdapter(StringNOventAdapter):
    eigenzeit = fractions.Fraction(1, 8)

    def __call__(self, novent: lily.NOvent) -> None:
        novent.string_contact_point = attachments.StringContactPoint("pizzicato")
        novent.volume = 2.3


class SimpleStringMaker(StringMaker):
    """Class for the generation of musical content that shall be played by strings.

    Additional parameters to tweak the musical result include:
        ...

        paramters concerning the splitting algorithm of long harmonic - pitches:

        - harmonic_pitches_density (0, 1)
            for harmonic_pitches_density=1, no rests are accepted while a value == 0
            doesn't contain any sound

        - harmonic_pitches_activity (0, 1)
            for harmonic_pitches_activity=1 each possible beat contains a new attack,
            while 0 means that only one beat contains an attack.
    """

    _track_class = String

    def __init__(
        self,
        instrument: abjad.Instrument,
        novent_adapter_maker: infit.InfIt = infit.Cycle(
            (
                ArcoAdapter(),
                PizzAdapter(),
                ArcoAdapter(),
                # StaccatoAdapter(),
                # TremoloAdapter(),
                PizzAdapter(),
                ArcoAdapter(),
            )
        ),
        harmonic_pitches_density: float = 0.75,
        harmonic_pitches_activity: float = 0.275,
        harmonic_pitches_min_event_size: fractions.Fraction = fractions.Fraction(3, 16),
        harmonic_pitches_max_event_size: fractions.Fraction = fractions.Fraction(3, 4),
        optional_pitches_min_size: fractions.Fraction = fractions.Fraction(1, 8),
    ) -> None:
        super().__init__(instrument)

        self.novent_adapter_maker = novent_adapter_maker

        try:
            assert harmonic_pitches_density >= harmonic_pitches_activity
        except AssertionError:
            msg = "'harmonic_pitches_density' has to be bigger or equal to "
            msg += "'harmonic_pitches_activity'."
            raise ValueError(msg)

        self.harmonic_pitches_density = harmonic_pitches_density
        self.harmonic_pitches_activity = harmonic_pitches_activity
        self.harmonic_pitches_min_event_size = harmonic_pitches_min_event_size
        self.harmonic_pitches_max_event_size = harmonic_pitches_max_event_size
        self.optional_pitches_min_size = optional_pitches_min_size

    @property
    def available_pitches(self) -> tuple:
        return globals_.SCALE_PER_INSTRUMENT[self.instrument.name]

    def add_transcription(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet
    ) -> None:
        def has_following_pitch(
            idx: int, operation=lambda x: x + 1, nth_iteration=0
        ) -> bool:
            if nth_iteration >= 2:
                return False

            try:
                has_previous_pitch = (
                    abs_trans[idx].pitch.normalize() in self.available_pitches
                )
            except IndexError:
                has_previous_pitch = False
            except AttributeError:
                has_previous_pitch = has_following_pitch(
                    operation(idx), operation, nth_iteration + 1
                )

            return has_previous_pitch

        sp_dec = infit.Cycle((0, 1))
        for area in segment_maker.areas:
            if (
                not area.pitch.is_empty
                and area.responsible_string_instrument.name == self.instrument.name
            ):
                pitch = tools.find_closest_item(
                    area.pitch, self.instrument.available_pitches
                )

                for ev_idx, event in enumerate(area.string_events):
                    volume = 0.685
                    start, stop, event_type = event

                    if ev_idx > 0 and event_type == 0:
                        dec = next(sp_dec)

                        # TODO(don't make random decision if pizz or ordinario:
                        # better find the shortest note and decide this one shall be pizz
                        # or alternatively the last note) ... make also only pizz. at
                        # those positions that are inhabitated by both sine wave gen and
                        # by string instrument.
                        if dec == 1:
                            string_contact_point = attachments.StringContactPoint(
                                "pizzicato"
                            )
                            tremolo = None
                            volume = 2.2
                        else:
                            string_contact_point = attachments.StringContactPoint(
                                "ordinario"
                            )
                            tremolo = None
                    else:
                        string_contact_point = attachments.StringContactPoint(
                            "ordinario"
                        )
                        tremolo = None

                    novent = lily.NOvent(
                        delay=start,
                        duration=stop,
                        volume=volume,
                        hauptstimme=attachments.Hauptstimme(True),
                        string_contact_point=string_contact_point,
                        tremolo=tremolo,
                    )

                    self.attach_pitches_to_novent([pitch], novent)
                    nset.append(novent)

                for non_event in area.non_string_events:
                    start, stop = non_event
                    novent = lily.NOvent(
                        pitch=[],
                        delay=start,
                        duration=stop,
                        volume=0,
                        hauptstimme=attachments.Hauptstimme(True),
                    )
                    nset.append(novent)

        abs_trans = segment_maker.musdat["transcription"].convert2absolute()

        for idx, tone in enumerate(abs_trans):
            if not tone.pitch:
                has_following = has_following_pitch(idx + 1)
                has_previous = has_following_pitch(idx - 1, lambda x: x - 1)
                if has_following and has_previous:
                    novent = lily.NOvent(
                        pitch=[],
                        delay=tone.delay,
                        duration=tone.duration,
                        volume=0.685,
                        hauptstimme=attachments.Hauptstimme(True),
                    )
                    nset.append(novent)

    def _find_harmonic_pitch_areas(self, segment_maker: mus.SegmentMaker) -> tuple:
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop

        harmonic_pitch_areas = []

        for harmonic_pitch_novent in segment_maker.musdat["harmonic_pitches"]:

            pitch = harmonic_pitch_novent.pitch[0]
            slice_start, slice_stop = (
                fractions.Fraction(v)
                for v in (harmonic_pitch_novent.delay, harmonic_pitch_novent.duration)
            )

            # making copies for start / stop - values
            start, stop = (fractions.Fraction(v) for v in (slice_start, slice_stop))

            if pitch.normalize() in self.available_pitches:
                if slice_start != 0:
                    previous_slices = segment_maker.bread.find_responsible_slices(
                        0, slice_start
                    )
                else:
                    previous_slices = tuple([])

                if slice_stop != segment_maker.duration:
                    following_slices = segment_maker.bread.find_responsible_slices(
                        slice_stop, segment_maker.duration
                    )
                else:
                    following_slices = tuple([])

                for previous_slice in reversed(previous_slices):
                    if (
                        previous_slice.harmonic_field
                        and pitch.normalize() in previous_slice.harmonic_field
                    ):
                        start = fractions.Fraction(previous_slice.start)
                    else:
                        break

                for following_slice in following_slices:
                    if (
                        following_slice.harmonic_field
                        and pitch.normalize() in following_slice.harmonic_field
                    ):
                        stop = fractions.Fraction(following_slice.stop)
                    else:
                        break

                harmonic_pitch_area = HarmonicPitchArea(
                    pitch, start, stop, slice_start, slice_stop, spread_metrical_loop
                )

                harmonic_pitch_areas.append(harmonic_pitch_area)

        return tuple(harmonic_pitch_areas)

    @staticmethod
    def _repair_potential_collision_of_harmonic_pitch_areas(
        nset: lily.NOventSet, harmonic_pitch_areas: tuple
    ) -> None:
        # (1) first check for potential collisions with transcription tones
        for harmonic_pitch_area in harmonic_pitch_areas:
            if nset.is_occupied(
                harmonic_pitch_area.start, harmonic_pitch_area.stop, ignore_rests=False
            ):
                if nset.is_occupied(
                    harmonic_pitch_area.start,
                    harmonic_pitch_area.slice_stop,
                    ignore_rests=False,
                ):
                    if nset.is_occupied(
                        harmonic_pitch_area.slice_start,
                        harmonic_pitch_area.stop,
                        ignore_rests=False,
                    ):
                        harmonic_pitch_area.start = harmonic_pitch_area.slice_start
                        harmonic_pitch_area.stop = harmonic_pitch_area.slice_stop

                    else:
                        harmonic_pitch_area.start = harmonic_pitch_area.slice_start

                else:
                    harmonic_pitch_area.stop = harmonic_pitch_area.slice_stop

            assert not nset.is_occupied(
                harmonic_pitch_area.start, harmonic_pitch_area.stop, ignore_rests=False
            )

        # (2) check for potential collisions between consecutive harmonic pitch areas.
        for area0, area1 in zip(harmonic_pitch_areas, harmonic_pitch_areas[1:]):
            if area0.stop > area1.start:
                if area0.slice_stop == area0.stop:
                    area1.start = fractions.Fraction(area0.stop)
                elif area1.slice_start == area1.start:
                    area0.stop = fractions.Fraction(area1.start)
                else:
                    if area0.potential_duration > area1.potential_duration:
                        area0.stop = fractions.Fraction(area1.start)
                    else:
                        area1.start = fractions.Fraction(area0.stop)

    def _get_novent_adapter_for_splitted_harmonic_novents(
        self,
        n_attacks: int,
        positions_without_metricity: tuple,
        prefered_positions: tuple,
    ) -> tuple:
        novent_adapters = tuple(
            next(self.novent_adapter_maker) for n in range(n_attacks)
        )

        max_duration_per_prefered_position = tuple(
            b - a
            for a, b in zip(
                prefered_positions,
                prefered_positions[1:] + (positions_without_metricity[-1],),
            )
        )
        prefered_positions_sorted_by_max_duration = iter(
            sorted(
                prefered_positions,
                key=lambda pos: max_duration_per_prefered_position[
                    prefered_positions.index(pos)
                ],
            )
        )
        sorted_novent_adapters = [None for i in range(n_attacks)]
        for novent_adapter in novent_adapters:
            if novent_adapter.eigenzeit:
                idx = prefered_positions.index(
                    next(prefered_positions_sorted_by_max_duration)
                )
                sorted_novent_adapters[idx] = novent_adapter

        for novent_adapter in novent_adapters:
            if not novent_adapter.eigenzeit:
                idx = prefered_positions.index(
                    next(prefered_positions_sorted_by_max_duration)
                )
                sorted_novent_adapters[idx] = novent_adapter

        return tuple(sorted_novent_adapters)

    def _make_splitted_harmonic_novents(
        self,
        pitches: list,
        harmonic_pitch_volume: float,
        harmonic_pitch_area: HarmonicPitchArea,
    ) -> tuple:
        positions = harmonic_pitch_area.positions
        positions_without_metricity = tuple(map(operator.itemgetter(0), positions))
        n_positions = len(positions)
        n_attacks = int(n_positions * self.harmonic_pitches_activity)
        n_non_rest_positions = int(n_positions * self.harmonic_pitches_density)

        if n_attacks == 0 and self.harmonic_pitches_activity > 0:
            n_attacks = 1

        if n_non_rest_positions == 0 and self.harmonic_pitches_density > 0:
            n_non_rest_positions = 1

        prefered_positions = (positions_without_metricity[0],)
        prefered_positions += tuple(
            sorted(
                map(
                    operator.itemgetter(0),
                    sorted(positions[1:-1], key=operator.itemgetter(1), reverse=True)[
                        : n_attacks - 1
                    ],
                )
            )
        )

        if n_attacks == 1:
            novent_adapters = (ArcoAdapter(),)
        else:
            novent_adapters = self._get_novent_adapter_for_splitted_harmonic_novents(
                n_attacks, positions_without_metricity, prefered_positions
            )

        novents = []

        avervage_duration_per_attack = n_non_rest_positions / n_attacks

        for pf_pos_idx, start, novent_adapter in zip(
            range(n_attacks), prefered_positions, novent_adapters
        ):
            avervage_duration_per_attack = n_non_rest_positions / (
                n_attacks - pf_pos_idx
            )
            if n_non_rest_positions <= 0.5:
                break

            start_idx = positions_without_metricity.index(start)
            try:
                max_stop_idx = positions_without_metricity.index(
                    prefered_positions[pf_pos_idx + 1]
                )
            except IndexError:
                max_stop_idx = n_positions - 1

            if novent_adapter.eigenzeit:
                prefered_stop_idx = start_idx + 1
                last_position = positions_without_metricity[prefered_stop_idx]
                while last_position < novent_adapter.eigenzeit:
                    prefered_stop_idx += 1
                    try:
                        last_position = positions_without_metricity[prefered_stop_idx]
                    except IndexError:
                        prefered_stop_idx -= 1
                        break

            else:
                prefered_stop_idx = start_idx + int(avervage_duration_per_attack)

            stop_idx = min((prefered_stop_idx, max_stop_idx))
            stop = positions_without_metricity[stop_idx]

            novent = lily.NOvent(
                delay=start, duration=stop, volume=harmonic_pitch_volume,
            )
            self.attach_pitches_to_novent(pitches, novent)

            novent_adapter(novent)
            novents.append(novent)

            n_non_rest_positions -= stop_idx - start_idx

        return tuple(novents)

    def add_harmonic_pitches(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet,
    ) -> None:

        harmonic_pitch_areas = self._find_harmonic_pitch_areas(segment_maker)
        self._repair_potential_collision_of_harmonic_pitch_areas(
            nset, harmonic_pitch_areas
        )

        harmonic_pitch_volume = 0.5

        for hpa in harmonic_pitch_areas:
            positions = hpa.positions
            n_positions = len(positions)

            try:
                max_position_difference = positions[-1][0] - positions[0][0]
                if max_position_difference == 0:
                    max_position_difference = None
            except IndexError:
                max_position_difference = None

            pitches = [hpa.pitch]

            # (1) if the area is very short, make only one arco note and potentially
            # extend the area.
            if n_positions in (0, 1) or all(
                (
                    n_positions > 1,
                    max_position_difference < self.harmonic_pitches_min_event_size,
                )
            ):
                if n_positions == 0:
                    start, stop = hpa.slice_start, hpa.slice_stop
                else:
                    start, stop = positions[0][0], hpa.stop
                    if (stop - start) < self.harmonic_pitches_min_event_size:
                        start = hpa.start

                novent = lily.NOvent(
                    delay=start,
                    duration=stop,
                    volume=harmonic_pitch_volume,
                    string_contact_point=attachments.StringContactPoint("ordinario"),
                )
                self.attach_pitches_to_novent(pitches, novent)

                nset.append(novent)

            # (2) if the area is just within the allowed area, make a usual arco note.
            elif max_position_difference <= self.harmonic_pitches_max_event_size:
                start, stop = positions[0][0], positions[-1][0]

                novent = lily.NOvent(
                    delay=start,
                    duration=stop,
                    volume=harmonic_pitch_volume,
                    string_contact_point=attachments.StringContactPoint("ordinario"),
                )
                self.attach_pitches_to_novent(pitches, novent)

                nset.append(novent)

            # (3) if the area is particularily big, split the area in smaller entities
            else:
                for novent in self._make_splitted_harmonic_novents(
                    pitches, harmonic_pitch_volume, hpa
                ):
                    nset.append(novent)

    def _make_position_metricity_pitch_data_per_non_defined_area(
        self,
        segment_maker: mus.SegmentMaker,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        non_defined_areas: tuple,
    ) -> tuple:
        position_metricity_pitch_data_per_area = []
        for area in non_defined_areas:
            start, stop = area
            # available_positions_and_metricity
            apam = spread_metrical_loop.get_rhythm_metricity_pairs_for_instrument(
                self.instrument.name, start, stop
            )
            # divided by rests
            divided_positions_metricity_pitch_trios = []
            positions_metricity_pitch_trios = []
            for position_and_metricity0, position_and_metricity1 in zip(
                apam, apam[1:] + ((area[-1], None),)
            ):
                slice_ = segment_maker.bread.find_responsible_slices(
                    position_and_metricity0[0], position_and_metricity1[0]
                )[0]

                if slice_.harmonic_field:
                    available_pitches = tuple(
                        pitch
                        for pitch in slice_.harmonic_field
                        if pitch in self.available_pitches
                        and pitch != slice_.melody_pitch
                        and pitch != slice_.harmonic_pitch
                    )

                else:
                    available_pitches = tuple([])

                if available_pitches:
                    positions_metricity_pitch_trios.append(
                        position_and_metricity0 + (available_pitches,)
                    )
                else:
                    if positions_metricity_pitch_trios:
                        divided_positions_metricity_pitch_trios.append(
                            tuple(positions_metricity_pitch_trios)
                        )
                        positions_metricity_pitch_trios = []

            if positions_metricity_pitch_trios:
                divided_positions_metricity_pitch_trios.append(
                    tuple(positions_metricity_pitch_trios)
                )
                positions_metricity_pitch_trios = []

            if divided_positions_metricity_pitch_trios:
                position_metricity_pitch_data_per_area.extend(
                    tuple(divided_positions_metricity_pitch_trios)
                )

        return tuple(position_metricity_pitch_data_per_area)

    @staticmethod
    def _op_find_overlapping_vectors(vectors: tuple) -> tuple:
        vector_areas = dict([])
        for vector in vectors:
            va = vector[:2]
            pitch = vector[2]

            if va not in vector_areas:
                vector_areas.update({va: set([])})

            vector_areas[va].add(pitch)

        return tuple((key, tuple(value)) for key, value in vector_areas.items())

    @staticmethod
    def _op_repair_vector_collision(vectors: tuple) -> tuple:
        vectors = list(vectors)
        for vector0, vector1 in itertools.combinations(vectors, 2):
            start0, stop0, start1, stop1 = vector0[0] + vector1[0]
            is_overlapping = not (stop0 <= start1 or stop1 <= start0)
            if is_overlapping and vector0 in vectors and vector1 in vectors:
                span0, span1 = stop0 - start0, stop1 - start1
                if span1 > span0:
                    smaller = vector0
                else:
                    smaller = vector1

                del vectors[vectors.index(smaller)]
        return tuple(vectors)

    def _op_make_novents_from_vectors(
        self, vectors: tuple, area: tuple, segment_maker: mus.SegmentMaker
    ) -> tuple:
        optional_pitch_volume = 0.3
        optional_pitch_novent_adapter = ArcoAdapter()

        novents = []
        for vector in vectors:
            start, stop = (area[idx][0] for idx in vector[0])
            pitches = vector[1]

            pitches2compare = set([])
            for slice_ in segment_maker.bread.find_responsible_slices(start, stop):
                pitches2compare.add(slice_.melody_pitch)
                pitches2compare.add(slice_.harmonic_pitch)

            if len(pitches) > 1:

                # pitch_getter_function
                def pgf(instr):
                    return instr.normal_pitches

            else:

                # pitch_getter_function
                def pgf(instr):
                    return instr.available_pitches

            registered_pitches = []
            for pitch in pitches:
                registered_pitches.append(
                    segment_maker._register_harmonic_pitch(
                        pitches2compare,
                        pitch,
                        get_available_pitches_from_adapted_instrument=pgf,
                    )
                )

            novent = lily.NOvent(
                delay=start,
                duration=stop,
                volume=optional_pitch_volume,
                optional=attachments.Optional(),
            )

            if len(pitches) > 1:
                novent.choose = attachments.ChooseOne()

            self.attach_pitches_to_novent(registered_pitches, novent)
            optional_pitch_novent_adapter(novent)

            novents.append(novent)

        return tuple(novents)

    def _op_extract_vectors_from_area(self, area: tuple) -> tuple:
        used_pitches_per_point = [[] for i in area]
        vectors = []

        for point_idx, point in enumerate(area[:-1]):
            for pitch in point[2]:
                if pitch not in used_pitches_per_point[point_idx]:
                    for higher_point_idx, point1 in enumerate(
                        area[point_idx + 1 :]
                    ):
                        higher_point_idx += point_idx + 1
                        if pitch in point1[2]:
                            used_pitches_per_point[higher_point_idx].append(pitch)
                        else:
                            higher_point_idx -= 1
                            break

                    span = higher_point_idx - point_idx
                    real_span = area[higher_point_idx][0] - area[point_idx][0]
                    if span > 0 and real_span >= self.optional_pitches_min_size:
                        if span > 1:
                            # check if one point later the metricity is higher than
                            # the current position. if so choose this one.
                            if area[point_idx][1] < area[point_idx + 1][1]:
                                if (
                                    area[higher_point_idx][0]
                                    - area[point_idx + 1][0]
                                ) >= self.optional_pitches_min_size:
                                    point_idx += 1

                            span = higher_point_idx - point_idx

                        vector = (
                            int(point_idx),
                            int(higher_point_idx),
                            pitch,
                        )
                        vectors.append(vector)

        return tuple(vectors)

    def add_optional_pitches(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet,
    ) -> None:
        non_defined_areas = nset.detect_undefined_areas()
        non_defined_areas = tuple(
            filter(
                lambda area: (area[1] - area[0]) >= self.optional_pitches_min_size,
                non_defined_areas,
            )
        )
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop

        # position_metricity_pitch_data_per_area
        pmpdpa = self._make_position_metricity_pitch_data_per_non_defined_area(
            segment_maker, spread_metrical_loop, non_defined_areas
        )

        for area in pmpdpa:
            vectors = self._op_extract_vectors_from_area(area)
            if vectors:
                vectors = self._op_find_overlapping_vectors(vectors)
                vectors = self._op_repair_vector_collision(vectors)

                for novent in self._op_make_novents_from_vectors(
                    vectors, area, segment_maker
                ):
                    nset.append(novent)

    @staticmethod
    def _detect_hauptstimme_groups(nline: lily.NOventLine) -> tuple:
        indices = []
        split_indices = []

        for event_idx, event in enumerate(nline):
            if event.hauptstimme:
                if event.hauptstimme.is_hauptstimme:
                    if indices:
                        if indices[-1] + 1 != event_idx:
                            split_indices.append(len(indices))
                    indices.append(event_idx)

        if indices:
            return tuple(tuple(g) for g in np.split(indices, split_indices))
        else:
            return tuple([])

    @staticmethod
    def _manage_hauptstimme_attachments(nline: lily.NOventLine) -> None:
        groups = SimpleStringMaker._detect_hauptstimme_groups(nline)
        for group in groups:
            if len(group) == 1:
                nline[group[0]].hauptstimme.is_once = True
            else:
                nline[group[-1]].hauptstimme.is_hauptstimme = False

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        nlset = lily.NOventSet(size=segment_maker.duration)

        self.add_transcription(segment_maker, nlset)
        self.add_harmonic_pitches(segment_maker, nlset)
        self.add_optional_pitches(segment_maker, nlset)

        nline = nlset.novent_line
        nline = nline.tie_pauses()

        self._manage_hauptstimme_attachments(nline)

        has_been_set = False
        for event in nline:
            if event.hauptstimme is None:
                if has_been_set is True:
                    event.hauptstimme = attachments.Hauptstimme(False)

            elif event.hauptstimme.is_hauptstimme:
                has_been_set = True

        return self._prepare_staves(nline, segment_maker)
