"""Simple sampler for generating simulations of string instruments.

It uses the open-source VSCO-2 sample package.

The expected sample paths are
    .local/share/sounds/Solo_Contrabass
    .local/share/sounds/Solo_Violin
"""

import numpy as np
import os
import json
import random

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

from aml import comprovisation
from aml import globals_


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
        diskin2 = "{} diskin2 p4, p5, 0, 1, 6, 4".format(", ".join(name_of_signals))
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

        if novent.tremolo:
            pt = ("trem",)

        elif novent.string_contact_point == attachments.StringContactPoint("pizzicato"):
            pt = ("pizz",)

        else:
            pt = ("susvib", "arcovib")

        allowed_samples = tuple(
            sorted(
                tuple(s for s in self.samples if s.playing_technique in pt),
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
                (abjad_pitch, added_pitch)
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


class SimpleStringMaker(StringMaker):
    _track_class = String

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

        abs_trans = segment_maker.musdat["transcription"].convert2absolute()
        for idx, tone in enumerate(abs_trans):

            if tone.pitch:
                if tone.pitch.normalize() in self.available_pitches:
                    pitch = tools.find_closest_item(
                        tone.pitch, self.instrument.available_pitches
                    )
                    novent = lily.NOvent(
                        delay=tone.delay,
                        duration=tone.duration,
                        volume=0.8,
                        hauptstimme=attachments.Hauptstimme(True),
                    )

                    self.attach_pitches_to_novent([pitch], novent)
                    nset.append(novent)

            else:
                has_following = has_following_pitch(idx + 1)
                has_previous = has_following_pitch(idx - 1, lambda x: x - 1)
                if has_following and has_previous:
                    novent = lily.NOvent(
                        pitch=[],
                        delay=tone.delay,
                        duration=tone.duration,
                        volume=0.8,
                        hauptstimme=attachments.Hauptstimme(True),
                    )
                    nset.append(novent)

    def add_harmonic_pitches(
        self, segment_maker: mus.SegmentMaker, nset: lily.NOventSet
    ) -> None:
        add_tremolo = infit.Cycle((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        for h_novent in segment_maker.musdat["harmonic_pitches"]:

            pitch = h_novent.pitch[0]

            if pitch.normalize() in self.available_pitches:

                novent = lily.NOvent(
                    delay=h_novent.delay, duration=h_novent.duration, volume=0.75
                )

                self.attach_pitches_to_novent([pitch], novent)

                if next(add_tremolo):
                    novent.tremolo = attachments.Tremolo()

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
