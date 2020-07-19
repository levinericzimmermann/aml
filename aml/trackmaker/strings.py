"""Simple sampler for generating simulations of string instruments.

It uses the open-source VSCO-2 sample package.

The expected sample paths are
    .local/share/sounds/Solo_Contrabass
    .local/share/sounds/Solo_Violin
"""

import abc
import functools
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
from mu.utils import interpolations
from mu.utils import tools

from mutools import attachments
from mutools import mus
from mutools import lily
from mutools import synthesis

from aml import areas
from aml import complex_meters
from aml import comprovisation
from aml import globals_
from aml import tweaks

from aml.trackmaker import general


####################################################################################
#                            defining TrackClass                                   #
####################################################################################


class String(general.AMLTrack):
    _orientation_staff_size = -4

    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        title: str = None,
        resolution: int = None,
    ):

        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"),
            abjad_data[0][0][0],
        )
        abjad_data[2].lilypond_type = "RhythmicStaff"

        for orientation_staff in (abjad_data[0], abjad_data[2]):
            abjad.detach(abjad.MetronomeMark, orientation_staff[0][0])
            abjad.setting(orientation_staff).font_size = self._orientation_staff_size
            magstep = abjad.Scheme(["magstep", self._orientation_staff_size])
            abjad.override(orientation_staff).staff_symbol.thickness = magstep
            abjad.override(orientation_staff).staff_symbol.staff_space = magstep

        for literal in (
            "\\accidentalStyle dodecaphonic-first",
            "\\override StemTremolo.slope = #0.37",
            "\\override StemTremolo.beam-thickness = #0.3",
            "\\override StemTremolo.beam-width = #1.35",
        ):
            abjad.attach(
                abjad.LilyPondLiteral(literal, "before"), abjad_data[1][0][0],
            )

        super().__init__(abjad_data, sound_engine, title, resolution)


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

    # remove_files = False
    # print_output = True

    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )

    @property
    def cname(self) -> str:
        return ".string_sampler"

    @property
    def orc(self) -> str:
        def make_sampler_instr(n_glissando_points: int) -> str:
            if n_glissando_points == 0:
                pitchseg = "kpitch = p6"

            else:
                pitchseg = "kpitch linseg "
                pitchseg_items = []
                nth_p = 6
                for point_idx in range((n_glissando_points * 2) - 1):
                    pitchseg_items.append("p{}".format(nth_p + point_idx))
                pitchseg += ", ".join(pitchseg_items)

            summarized = " + ".join(
                tuple(
                    signal
                    for sig_idx, signal in enumerate(name_of_signals)
                    if sig_idx in channel2use
                )
            )
            lines = [
                "instr {}".format(n_glissando_points + 1),
                pitchseg,
                "kvol linseg 0, 0.1, 1, p3 - 0.2, 1, 0.1, 0",
                "{} diskin2 p4, kpitch, 0, 0, 6, 4".format(", ".join(name_of_signals)),
                "aSummarized = ({}) / {}".format(summarized, len(channel2use)),
                "asig = aSummarized * kvol * p5",
                "gaSendL  =        gaSendL + asig/3",
                "gaSendR  =        gaSendR + asig/3",
                "out asig",
                "endin\n",
            ]
            return "\n".join(lines)

        n_channels = 2
        channel2use = tuple(range(n_channels))

        name_of_signals = tuple("aSignal{}".format(idx) for idx in range(n_channels))

        basic_lines = (
            "0dbfs=1",
            "gisine  ftgen	0,0,4096,10,1",
            "gaSendL, gaSendR init 0",
            "nchnls=1\n",
            "instr 100",
            "aRvbL,aRvbR reverbsc gaSendL,gaSendR,0.695,7000",
            "out     (aRvbL + aRvbR) * 0.385",
            "clear    gaSendL,gaSendR",
            "endin\n",
        )

        lines = "\n".join(basic_lines)
        n_glissando_points_per_novent = set(
            len(novent.glissando.pitch_line) if novent.glissando else 0
            for novent in self._novent_line
        )
        for n_glissando_points in n_glissando_points_per_novent:
            lines += "\n"
            lines += make_sampler_instr(n_glissando_points)

        return lines

    @property
    def sco(self) -> str:
        lines = ["i100 0 {}".format(float(self._novent_line.duration))]
        for novent_abs, novent in zip(
            self._novent_line.convert2absolute(), self._novent_line
        ):

            n_glissando_point = (
                len(novent.glissando.pitch_line) if novent.glissando else 0
            )
            samples = self.find_samples(novent)
            delay, duration = float(novent_abs.delay), float(novent.duration)
            volume = novent.volume
            if not volume:
                volume = 1
            else:
                volume = float(volume)

            for sample, expected_freq in samples:
                pitch_factor = expected_freq / sample.freq
                line = 'i{} {} {} "{}" {}'.format(
                    n_glissando_point + 1,
                    delay,
                    duration,
                    os.path.relpath(sample.path),
                    volume,
                )

                if n_glissando_point == 0:
                    line += " {}".format(pitch_factor)

                else:
                    duration_per_point = tuple(
                        pi.delay for pi in novent.glissando.pitch_line
                    )[:-1]
                    pitch_factor_per_point = tuple(
                        (float(pi.pitch + novent.pitch[0]) * globals_.CONCERT_PITCH)
                        / sample.freq
                        for pi in novent.glissando.pitch_line
                    )
                    line += " {}".format(pitch_factor_per_point[0])
                    for duration, pitch_factor in zip(
                        duration_per_point, pitch_factor_per_point[1:]
                    ):
                        line += " {} {}".format(float(duration), pitch_factor)

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


class StringMaker(general.AMLTrackMaker):
    def __init__(self, instrument: abjad.Instrument) -> None:
        self.instrument = instrument

    def attach_pitches_to_novent(
        self, pitches: tuple, novent: lily.NOvent, force_harmonic: bool = False
    ) -> None:
        for p in pitches:
            assert p in self.instrument.available_pitches

        novent.pitch = pitches

        if force_harmonic:
            assert pitches[0] - ji.r(4, 1) in self.instrument.normal_pitches

        if pitches[0] in self.instrument.harmonic_pitches or force_harmonic:
            (
                abjad_pitch,
                added_pitch,
            ) = self._get_abjad_pitch_and_added_pitch_for_harmonic_pitch(pitches[0])
            novent.artifical_harmonic = attachments.ArtificalHarmonicAddedPitch(
                abjad.PitchSegment((abjad_pitch, added_pitch))
            )

    def _get_abjad_pitch_and_added_pitch_for_harmonic_pitch(
        self, pitch: ji.JIPitch
    ) -> tuple:
        abjad_pitch = lily.convert2abjad_pitch(
            pitch - ji.r(4, 1), globals_.RATIO2PITCHCLASS
        )
        (
            added_pitch_class,
            octave_change,
        ) = globals_.RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE[
            pitch.normalize()
        ]
        added_pitch = abjad.NamedPitch(
            abjad.NamedPitchClass(added_pitch_class),
            octave=int(abjad_pitch.octave) + octave_change,
        )
        return tuple(sorted((abjad_pitch, added_pitch)))

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return STRING_SOUND_ENGINE(
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[1])
        )

    def _prepare_staves(
        self, polyline: old.PolyLine, segment_maker: mus.SegmentMaker
    ) -> old.PolyLine:

        # add crucial notation elements
        polyline[1][0].clef = attachments.Clef(
            {"cello": "bass", "viola": "alto", "violin": "treble"}[self.instrument.name]
        )
        # polyline[1][0].margin_markup = attachments.MarginMarkup(
        #     "{}.{}".format(segment_maker.chapter, segment_maker.verse)
        # )

        for nol in polyline:
            nol[0].tempo = attachments.Tempo((1, 4), segment_maker.tempo)

        return polyline


class SilentStringMaker(StringMaker):
    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        dur = segment_maker.duration
        nline = lily.NOventLine([lily.NOvent(duration=dur, delay=dur)])
        return old.PolyLine(
            [
                segment_maker.melodic_orientation,
                nline,
                segment_maker.rhythmic_orientation,
            ]
        )

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

    def __eq__(self, other) -> bool:
        try:
            return type(self).__name__ == type(other).__name__
        except AttributeError:
            return False


class ArcoAdapter(StringNOventAdapter):
    def __call__(self, novent: lily.NOvent) -> None:
        novent.string_contact_point = attachments.StringContactPoint("arco")


class StaccatoAdapter(StringNOventAdapter):
    eigenzeit = fractions.Fraction(1, 8)

    def __call__(self, novent: lily.NOvent) -> None:
        novent.string_contact_point = attachments.StringContactPoint("arco")
        novent.articulation_once = attachments.ArticulationOnce(".")


class TremoloAdapter(StringNOventAdapter):
    def __call__(self, novent: lily.NOvent) -> None:
        novent.tremolo = attachments.Tremolo()
        novent.string_contact_point = attachments.StringContactPoint("arco")
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
    _acciaccatura_duration = abjad.Duration(1, 8)

    def __init__(
        self,
        instrument: abjad.Instrument,
        pizz_maker: infit.InfIt = infit.ActivityLevel(3),
        acciaccatura_maker: infit.InfIt = infit.ActivityLevel(7),
        force_acciaccatura_to_glissando_maker: infit.InfIt = infit.ActivityLevel(0),
        acciaccatura_glissando_size_maker: infit.InfIt = infit.Cycle((0, 1, 0)),
        glissando_maker: infit.InfIt = infit.ActivityLevel(8),
        after_glissando_maker: infit.InfIt = infit.ActivityLevel(10),
        tremolo_maker: infit.InfIt = infit.ActivityLevel(4),
        harmonic_pitches_density: float = 0.8,
        harmonic_pitches_activity: float = 0.6,
        harmonic_pitches_min_event_size: fractions.Fraction = fractions.Fraction(3, 16),
        harmonic_pitches_max_event_size: fractions.Fraction = fractions.Fraction(2, 4),
        shall_add_optional_pitches: bool = False,
        optional_pitches_min_size: fractions.Fraction = fractions.Fraction(1, 16),
        optional_pitches_avg_size: fractions.Fraction = fractions.Fraction(3, 16),
        optional_pitches_maximum_octave_difference_from_melody_pitch: tuple = (1, 0),
        after_glissando_size=fractions.Fraction(1, 16),
    ) -> None:
        super().__init__(instrument)

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
        self.optional_pitches_avg_size = optional_pitches_avg_size
        self.optional_pitches_maximum_octave_difference_from_melody_pitch = (
            optional_pitches_maximum_octave_difference_from_melody_pitch
        )
        self.shall_add_optional_pitches = shall_add_optional_pitches

        self.pizz_maker = pizz_maker
        self.acciaccatura_maker = acciaccatura_maker
        self.force_acciaccatura_to_glissando_maker = (
            force_acciaccatura_to_glissando_maker
        )
        self.acciaccatura_glissando_size_maker = acciaccatura_glissando_size_maker
        self.glissando_maker = glissando_maker
        self.after_glissando_maker = after_glissando_maker
        self.after_glissando_size = after_glissando_size
        self.tremolo_maker = tremolo_maker

    def __call__(self) -> String:
        # OVERRIDING DEFAULT CALL METHOD TO MAKE SURE THE ORIENTATION LINES DON'T CONTAIN
        # TIME-SIGNATURES --- THIS IS A DIRTY HACK FOR AVOIDING LILYPOND-ISSUE FOR PRITING
        # TIME-SIGNATURES TWICE WHEN ONE VOICE HAS GRACE NOTES AT THE FIRST BEAT OF A BAR
        # WHILE OTHER VOICES DON'T. THE MENTIONED ISSUE IS DOCUMENTED ON THIS WEBPAGE:
        # https://lilypond.org/doc/v2.15/Documentation/notation/special-rhythmic-concerns.html

        # ---- see:
        # "Grace note synchronization can also lead to surprises. Staff notation, such as
        # key signatures, bar lines, etc., are also synchronized. Take care when you mix
        # staves with grace notes and staves without."

        # 1. make abjad data
        staves = []
        for line, add_time_signatures, repeated_areas in zip(
            self.musdat,
            (False, True, False),
            (tuple([]), self.repeated_areas, tuple([])),
        ):
            staves.append(
                self._convert_novent_line2abjad_staff(
                    line,
                    self.bars,
                    self.ratio2pitchclass_dict,
                    repeated_areas,
                    add_time_signatures=add_time_signatures,
                )
            )

        abjad_data = abjad.Container(staves)
        abjad_data.simultaneous = True

        # 2. generate sound engine
        sound_engine = self.make_sound_engine()

        return self._track_class(abjad_data, sound_engine, self.title)

    @property
    def available_pitches(self) -> tuple:
        return globals_.SCALE_PER_INSTRUMENT[self.instrument.name]

    #################################################################################
    #                    playing techniques / ornamentation methods                 #
    #################################################################################

    def _find_available_pitches_for_acciaccatura(
        self,
        segment_maker: mus.SegmentMaker,
        main_pitch: ji.JIPitch,
        start: fractions.Fraction,
        stop: fractions.Fraction,
    ) -> tuple:
        normalized_main_pitch = main_pitch.normalize()
        available_slices = segment_maker.bread.find_responsible_slices(start, stop)
        harmonic_fields = tuple(
            tuple(s.harmonic_field.keys()) for s in available_slices if s.harmonic_field
        )
        if harmonic_fields:
            available_pitches = set(functools.reduce(operator.add, harmonic_fields))
            available_pitches = tuple(
                filter(
                    lambda p: p in self.instrument.scale and p != normalized_main_pitch,
                    available_pitches,
                )
            )
            return available_pitches

        return tuple([])

    def _sort_pitch_classes_by_closness(
        self, main_pitch: ji.JIPitch, available_pitch_classes: tuple
    ) -> tuple:
        available_versions = functools.reduce(
            operator.add,
            (
                tuple(
                    p for p in self.instrument.available_pitches if p.normalize() == pc
                )
                for pc in available_pitch_classes
            ),
        )
        return tuple(
            sorted(available_versions, key=lambda p: abs(p - main_pitch).cents)
        )

    def find_acciaccatura(
        self,
        segment_maker: mus.SegmentMaker,
        main_pitch: ji.JIPitch,
        start: fractions.Fraction,
        stop: fractions.Fraction,
        is_harmonic: bool = False,
        add_glissando: bool = False,
        gliss_idx: int = None,
    ) -> attachments.Acciaccatura:
        available_pitch_classes = self._find_available_pitches_for_acciaccatura(
            segment_maker, main_pitch, start, stop
        )

        if not available_pitch_classes:
            add_glissando = True
            normalized_main_pitch = main_pitch.normalize()
            available_pitch_classes = tuple(
                p for p in self.instrument.scale if p != normalized_main_pitch
            )

        possible_pitches = self._sort_pitch_classes_by_closness(
            main_pitch, available_pitch_classes
        )

        if add_glissando:
            if not gliss_idx:
                gliss_idx = next(self.acciaccatura_glissando_size_maker)
            while gliss_idx >= len(possible_pitches):
                gliss_idx -= 1

            while gliss_idx < 0:
                gliss_idx += 1

            choosen_pitch = possible_pitches[gliss_idx]

        else:
            choosen_pitch = possible_pitches[0]

        if is_harmonic:
            assert choosen_pitch - ji.r(4, 1) in self.instrument.available_pitches

            ap0, ap1 = self._get_abjad_pitch_and_added_pitch_for_harmonic_pitch(
                choosen_pitch
            )
            abjad_note = abjad.Chord([ap0, ap1], self._acciaccatura_duration)
            abjad.tweak(abjad_note.note_heads[1]).style = "harmonic"

        else:
            abjad_note = abjad.Note(
                lily.convert2abjad_pitch(choosen_pitch, globals_.RATIO2PITCHCLASS),
                self._acciaccatura_duration,
            )

        return attachments.Acciaccatura(
            [choosen_pitch], abjad_note, add_glissando=add_glissando
        )

    #################################################################################
    #                    melodic pitches adding methods                             #
    #################################################################################

    def _filter_areas(self, areas: tuple) -> tuple:
        return tuple(
            filter(
                lambda area: not area.pitch.is_empty
                and area.responsible_string_instrument.name == self.instrument.name,
                areas,
            )
        )

    def _add_empty_notes_in_between_hauptstimme_rests(
        self, nset: lily.NOventSet, segment_maker: mus.SegmentMaker
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

    @staticmethod
    def _add_empty_string_notes_from_area(
        nset: lily.NOventSet, area: areas.Area
    ) -> None:
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

    def _detect_shall_play_pizz_per_event_in_area(self, area: areas.Area) -> tuple:
        allowed_events_for_pizz = tuple(
            filter(
                lambda event: event != area.string_events[0]
                and area.is_event_overlapping_with_sine_events(event),
                area.string_events,
            )
        )
        n_pizz_events = sum((next(self.pizz_maker) for _ in allowed_events_for_pizz))
        shall_play_pizz_per_event = []
        allowed_string_events_sorted_by_duration = sorted(
            allowed_events_for_pizz, key=lambda event: event[1] - event[0]
        )
        for event in area.string_events:
            shall_play_pizz = False
            if event in allowed_events_for_pizz:
                if (
                    allowed_string_events_sorted_by_duration.index(event)
                    < n_pizz_events
                ):
                    shall_play_pizz = True

            shall_play_pizz_per_event.append(shall_play_pizz)

        return tuple(shall_play_pizz_per_event)

    def _add_string_notes_from_area(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet, area: areas.Area
    ) -> None:
        volume = 0.685

        normalized_area_pitch = area.pitch.normalize()

        pitch = tools.find_closest_item(
            area.pitch,
            tuple(
                filter(
                    lambda p: p.normalize() == normalized_area_pitch,
                    self.instrument.available_pitches,
                )
            ),
        )

        shall_play_pizz_per_event = self._detect_shall_play_pizz_per_event_in_area(area)

        for event, shall_play_pizz in zip(
            area.string_events, shall_play_pizz_per_event
        ):
            start, stop, event_type = event

            if event_type == 0:
                shall_play_pizz = False

            if shall_play_pizz:
                string_contact_point = attachments.StringContactPoint("pizzicato")

            else:
                string_contact_point = attachments.StringContactPoint("arco")

            novent = lily.NOvent(
                delay=start,
                duration=stop,
                volume=volume,
                hauptstimme=attachments.Hauptstimme(True),
                string_contact_point=string_contact_point,
            )

            self.attach_pitches_to_novent([pitch], novent)

            if not shall_play_pizz or self._find_available_pitches_for_acciaccatura(
                segment_maker, pitch, start, stop
            ):
                if next(self.acciaccatura_maker):
                    novent.acciaccatura = self.find_acciaccatura(
                        segment_maker,
                        pitch,
                        start,
                        stop,
                        is_harmonic=bool(novent.artifical_harmonic),
                    )

            if not shall_play_pizz:
                if next(self.glissando_maker):
                    pass

            nset.append(novent)

    def add_transcription(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet
    ) -> None:
        for area in self._filter_areas(segment_maker.areas):
            self._add_string_notes_from_area(segment_maker, nset, area)
            self._add_empty_string_notes_from_area(nset, area)

        self._add_empty_notes_in_between_hauptstimme_rests(nset, segment_maker)

    #################################################################################
    #                   harmonic pitches adding methods                             #
    #################################################################################

    def _find_harmonic_pitch_areas(self, segment_maker: mus.SegmentMaker) -> tuple:
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop

        harmonic_pitch_areas = []

        for (
            harmonic_pitch_novent,
            melody_pitch_start_postitions,
        ) in segment_maker.musdat["harmonic_pitches"]:

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

                harmonic_pitch_areas.append(
                    (harmonic_pitch_area, melody_pitch_start_postitions)
                )

        return tuple(harmonic_pitch_areas)

    @staticmethod
    def _repair_potential_collision_of_harmonic_pitch_areas(
        nset: lily.NOventSet, harmonic_pitch_areas: tuple
    ) -> None:
        # (1) first check for potential collisions with transcription tones
        for harmonic_pitch_area, melody_pitch_start_postitions in harmonic_pitch_areas:
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
            area0, _ = area0
            area1, _ = area1
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
            PizzAdapter() if next(self.pizz_maker) else ArcoAdapter()
            for n in range(n_attacks)
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

    @staticmethod
    def _find_prefered_positions_for_splitted_harmonic_novents(
        positions: tuple,
        positions_without_metricity: tuple,
        n_attacks: int,
        melody_pitch_start_positions: tuple,
    ) -> tuple:
        prefered_positions = (positions_without_metricity[0],)
        first_position_idx = 0

        if (
            not melody_pitch_start_positions
            or positions_without_metricity[1] < melody_pitch_start_positions[0]
        ):
            if positions[0][1] < positions[1][1]:
                prefered_positions = (positions_without_metricity[1],)
                first_position_idx = 1

        prefered_positions += tuple(
            sorted(
                map(
                    operator.itemgetter(0),
                    sorted(
                        tuple(
                            position
                            for position_idx, position in enumerate(positions[:-1])
                            if first_position_idx != position_idx
                        ),
                        key=operator.itemgetter(1),
                        reverse=True,
                    )[: n_attacks - 1],
                )
            )
        )
        return tuple(sorted(prefered_positions))

    def _make_splitted_harmonic_novents(
        self,
        segment_maker: mus.SegmentMaker,
        pitches: list,
        harmonic_pitch_volume: float,
        harmonic_pitch_area: HarmonicPitchArea,
        melody_pitch_start_positions: tuple,
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

        prefered_positions = self._find_prefered_positions_for_splitted_harmonic_novents(
            positions,
            positions_without_metricity,
            n_attacks,
            melody_pitch_start_positions,
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

            if novent_adapter == PizzAdapter():
                if self._find_available_pitches_for_acciaccatura(
                    segment_maker, pitches[0], start, stop
                ):
                    if next(self.acciaccatura_maker):
                        novent.acciaccatura = self.find_acciaccatura(
                            segment_maker,
                            pitches[0],
                            start,
                            stop,
                            is_harmonic=bool(novent.artifical_harmonic),
                        )

            else:
                if next(self.tremolo_maker):
                    novent.tremolo = attachments.Tremolo()

                elif next(self.acciaccatura_maker):
                    novent.acciaccatura = self.find_acciaccatura(
                        segment_maker,
                        pitches[0],
                        start,
                        stop,
                        is_harmonic=bool(novent.artifical_harmonic),
                    )

                elif next(self.glissando_maker):
                    pass

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

        for hpa, melody_pitch_start_positions in harmonic_pitch_areas:
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
                    if (
                        stop - start
                    ) < self.harmonic_pitches_min_event_size and not nset.is_occupied(
                        hpa.start, start
                    ):
                        start = hpa.start

                novent = lily.NOvent(
                    delay=start,
                    duration=stop,
                    volume=harmonic_pitch_volume,
                    string_contact_point=attachments.StringContactPoint("arco"),
                )
                self.attach_pitches_to_novent(pitches, novent)

                if not nset.is_occupied(start, stop):
                    nset.append(novent)

            # (2) if the area is just within the allowed area, make a usual arco note.
            elif max_position_difference <= self.harmonic_pitches_max_event_size:
                start, stop = positions[0][0], positions[-1][0]

                novent = lily.NOvent(
                    delay=start,
                    duration=stop,
                    volume=harmonic_pitch_volume,
                    string_contact_point=attachments.StringContactPoint("arco"),
                )
                self.attach_pitches_to_novent(pitches, novent)

                nset.append(novent)

            # (3) if the area is particularily big, split the area in smaller entities
            else:
                for novent in self._make_splitted_harmonic_novents(
                    segment_maker,
                    pitches,
                    harmonic_pitch_volume,
                    hpa,
                    melody_pitch_start_positions,
                ):
                    nset.append(novent)

    #################################################################################
    #                   optional pitches adding methods                             #
    #################################################################################

    def _op_make_position_metricity_pitch_data_per_non_defined_area(
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

    def _op_extract_vectors_from_area(self, area: tuple) -> tuple:
        used_pitches_per_point = [[] for i in area]
        vectors = []

        for point_idx, point in enumerate(area[:-1]):
            for pitch in point[2]:
                if pitch not in used_pitches_per_point[point_idx]:
                    for higher_point_idx, point1 in enumerate(area[point_idx + 1 :]):
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
                                    area[higher_point_idx][0] - area[point_idx + 1][0]
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
                if slice_.melody_pitch:
                    pitches2compare.add(slice_.melody_pitch)
                if slice_.harmonic_pitch:
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
                        maximum_octave_difference=self.optional_pitches_maximum_octave_difference_from_melody_pitch,
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

    def _op_adapt_optional_novents(
        self, novent_line: lily.NOventLine, segment_maker: mus.SegmentMaker
    ) -> None:
        new_novent_line = []
        for idx, novent in enumerate(novent_line):
            splitted = False
            if novent.optional:
                if novent.delay > self.optional_pitches_avg_size:
                    split2n_items = int(novent.delay / self.optional_pitches_avg_size)
                    if split2n_items > 1:
                        new_novent_line.extend(
                            tweaks.split_by_structure(
                                idx,
                                split2n_items,
                                novent_line,
                                segment_maker,
                                change_novent_line=False,
                            )
                        )
                        splitted = True

            if not splitted:
                new_novent_line.append(novent)

        absolute_novent_line = tools.accumulate_from_zero(
            tuple(fractions.Fraction(item.delay) for item in new_novent_line)
        )
        for novent, start, stop in zip(
            new_novent_line, absolute_novent_line, absolute_novent_line[1:]
        ):
            if novent.optional:
                shall_play_pizz = bool(next(self.pizz_maker))
                if shall_play_pizz:
                    novent.string_contact_point = attachments.StringContactPoint(
                        "pizzicato"
                    )
                else:
                    novent.string_contact_point = attachments.StringContactPoint("arco")

                if (
                    not shall_play_pizz
                    or self._find_available_pitches_for_acciaccatura(
                        segment_maker, novent.pitch[0], start, stop
                    )
                ):
                    if len(novent.pitch) == 1 and next(self.acciaccatura_maker):
                        novent.acciaccatura = self.find_acciaccatura(
                            segment_maker,
                            novent.pitch[0],
                            start,
                            stop,
                            is_harmonic=bool(novent.artifical_harmonic),
                        )

        return lily.NOventLine(new_novent_line)

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
        pmpdpa = self._op_make_position_metricity_pitch_data_per_non_defined_area(
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

    #################################################################################
    #                 general methods for generating novent-line object             #
    #################################################################################

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

        has_been_set = False
        for event in nline:
            if event.hauptstimme is None:
                if has_been_set is True:
                    event.hauptstimme = attachments.Hauptstimme(False)

            elif event.hauptstimme.is_hauptstimme:
                has_been_set = True

    def _attach_after_glissando(self, novent_line: lily.NOventLine) -> None:
        for novent0, novent1 in zip(novent_line, novent_line[1:]):
            tests_if_after_glissando_could_get_attached = (
                novent0.pitch and novent1.pitch,
                novent0.string_contact_point
                != attachments.StringContactPoint("pizzicato"),
                not novent1.optional,
                not novent0.acciaccatura,
                novent0.pitch != novent1.pitch,
                novent0.duration >= self.after_glissando_size,
            )
            if all(tests_if_after_glissando_could_get_attached):
                interval = novent1.pitch[0] - novent0.pitch[0]
                if len(novent0.pitch) == 1 and abs(interval) <= ji.r(3, 2):
                    if next(self.after_glissando_maker):
                        novent0.glissando = old.GlissandoLine(
                            interpolations.InterpolationLine(
                                [
                                    old.PitchInterpolation(
                                        novent0.delay - self.after_glissando_size,
                                        ji.r(1, 1),
                                    ),
                                    old.PitchInterpolation(
                                        self.after_glissando_size, ji.r(1, 1)
                                    ),
                                    old.PitchInterpolation(0, interval),
                                ]
                            )
                        )

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        nlset = lily.NOventSet(size=segment_maker.duration)

        self.add_transcription(segment_maker, nlset)
        self.add_harmonic_pitches(segment_maker, nlset)
        if self.shall_add_optional_pitches:
            self.add_optional_pitches(segment_maker, nlset)

        nline = nlset.novent_line
        nline = nline.tie_pauses()

        nline = self._op_adapt_optional_novents(nline, segment_maker)
        self._attach_after_glissando(nline)
        self._manage_hauptstimme_attachments(nline)

        polyline = old.PolyLine(
            [
                segment_maker.melodic_orientation,
                nline,
                segment_maker.rhythmic_orientation,
            ]
        )
        return polyline
