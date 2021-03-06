import functools
import itertools
import json
import operator
import random
import subprocess

import quicktions as fractions

import abjad
import pyo

import crosstrainer

from mu.midiplug import midiplug

from mu.mel import ji
from mu.mel import mel
from mu.sco import old
from mu.utils import infit
from mu.utils import interpolations
from mu.utils import tools

from mutools import attachments
from mutools import lily
from mutools import mus
from mutools import synthesis

from aml import complex_meters
from aml import comprovisation
from aml import globals_

from aml.trackmaker import general

# from aml.electronics import midi as _right_hand_synth
# TODO(update _right_hand_synth!)
_right_hand_synth = None

KEYBOARD_SETUP_PATH = "aml/electronics"


LOWEST_MIDI_NOTE = 21  # starting from b, so that each zone is repeating at each new b
N_MIDI_NOTES_PER_ZONE = (
    14,
    3 * 12,
    3 * 12,
)  # 1 octave + 3 pitches, 3 octaves, 3 octaves


def _make_keyboard_zones() -> tuple:
    accumulated_zones = tools.accumulate_from_n(N_MIDI_NOTES_PER_ZONE, LOWEST_MIDI_NOTE)
    return tuple(zip(accumulated_zones, accumulated_zones[1:]))


ZONES = _make_keyboard_zones()


def _generate_keyboard_midi_note2ji_pitch_mapping():
    # each intonation is allowed to appear twice in each zone (pianoteq and sine waves).
    # the following tuple assigns in which register each intonation of one scale degree
    # will appear (3 subtuples because there are always three different intonations per
    # scale degree). each subtuple contains again two tuples. the first tuple contains
    # integer representing the register for the pianoteq-zone and the second tuple
    # contains integer representing the register for the sine-wave-zone of this
    # intonation.the order of the distribution is depending on how frequent the particular
    # intonation is globally appearing in the transcription of the recitation where the
    # first entry is reserved for the most frequent appearing intonation.
    distributed_register_for_scale_pitches = (
        ((-1, 0), (0, 1)),  # most frequent intonation
        ((-2, -1), (-1, 0)),  # second frequent intonation
        ((-2, 0), (-1, 1)),  # least frequent intonation
    )

    # each auxiliary pitch intonation is only allowed to appear once in each zone.
    # the following tuple contains 3 subtuples that indicate the register for this
    # particular intonation within the pianoteq (first entry) and the sine-wave zone
    # (second entry). the individual subtuples aren't sorted in any particular way.
    distributed_register_for_auxiliary_pitches = (
        ((0,), (-1,)),
        ((-1,), (0,)),
        ((-2,), (1,)),
    )

    # where 0 is b, 1 is c, ...
    available_chromatic_pitches_per_scale_degree = (
        (0, 1),  # 1
        (2, 3),  # 2
        (4, 5),  # 3
        (6,),  # 4 -> only one scale degree because 4 is an auxiliary pitch
        (7, 8),  # 5
        (9, 10),  # 6
        (11,),  # 7 -> only one scale degree because 7 is an auxiliary pitch
    )

    with open("aml/counted_intonations_in_all_transcriptions.json", "r") as f:
        counted_intonations_in_all_transcriptions = json.load(f)

    # the pianoteq zone contains pitches from B to b'
    # the sine wave zone contains pitches from b to b''
    available_register_per_zone = ((-2, -1, 0), (-1, 0, 1))

    midi_note2ji_pitch_mapping_per_zone = {
        "pianoteq": {mn: None for mn in range(*ZONES[1])},
        "sine": {mn: None for mn in range(*ZONES[2])},
    }

    for intonations, available_chromatic_pitches, frequency_per_intonation in zip(
        globals_.INTONATIONS_PER_SCALE_DEGREE,
        available_chromatic_pitches_per_scale_degree,
        counted_intonations_in_all_transcriptions,
    ):
        if len(available_chromatic_pitches) == 2:
            sorted_frequency_per_intonation = sorted(
                frequency_per_intonation, reverse=True
            )
            distribution_per_intonation = tuple(
                distributed_register_for_scale_pitches[
                    sorted_frequency_per_intonation.index(frequency)
                ]
                for frequency in frequency_per_intonation
            )

        else:
            distribution_per_intonation = distributed_register_for_auxiliary_pitches

        available_positions_per_octave_per_zone = tuple(
            tuple(
                tuple(
                    chromatic_pitch + (12 * n) + zone_start
                    for chromatic_pitch in available_chromatic_pitches
                )
                for n in range(len(available_register))
            )
            for zone_start, available_register in zip(
                (ZONES[1][0], ZONES[2][0]), available_register_per_zone
            )
        )

        available_pitches_per_octave_per_zone = [
            [[] for register in available_register]
            for available_register in available_register_per_zone
        ]

        for intonation, distribution in zip(intonations, distribution_per_intonation):
            for zone_idx, available_register_in_this_zone in enumerate(distribution):
                for register in available_register_in_this_zone:
                    register_idx = available_register_per_zone[zone_idx].index(register)
                    registered_pitch = intonation + ji.r(1, 1).register(register)
                    available_pitches_per_octave_per_zone[zone_idx][
                        register_idx
                    ].append(registered_pitch)

        for (
            zone_name,
            available_pitches_per_octave,
            available_positions_per_octave,
        ) in zip(
            ("pianoteq", "sine"),
            available_pitches_per_octave_per_zone,
            available_positions_per_octave_per_zone,
        ):
            for available_pitches, available_positions in zip(
                available_pitches_per_octave, available_positions_per_octave
            ):
                for position, pitch in zip(
                    available_positions, sorted(available_pitches)
                ):
                    midi_note2ji_pitch_mapping_per_zone[zone_name][position] = pitch

    return midi_note2ji_pitch_mapping_per_zone


REAL_AVAILABLE_PITCHES_FOR_GONG_ZONE = tuple(
    pitch - ji.r(2, 1)
    for pitch in functools.reduce(
        operator.add, globals_.FILTERED_INTONATIONS_PER_SCALE_DEGREE
    )[1:]
)

REAL_AVAILABLE_PITCHES_FOR_KENONG_ZONE = tuple(
    pitch
    for pitch in functools.reduce(
        operator.add, globals_.FILTERED_INTONATIONS_PER_SCALE_DEGREE
    )[1:]
)

SYMBOLIC_GONG_OCTAVE = -5
REAL_GONG_PITCH2SYMBOLIC_GONG_PITCH = {
    p: p.register(SYMBOLIC_GONG_OCTAVE) for p in REAL_AVAILABLE_PITCHES_FOR_GONG_ZONE
}
SYMBOLIC_GONG_PITCH2REAL_GONG_PITCH = {
    value: key for key, value in REAL_GONG_PITCH2SYMBOLIC_GONG_PITCH.items()
}


def _generate_keyboard_midi_note2ji_pitch_mapping_for_gong_zone(
    midi_note2ji_pitch_mapping_per_zone: dict,
) -> None:
    # pitches are set to octave c3 until c4
    midi_pitch2ji_pitch = {
        midi_pitch: ji_pitch
        for midi_pitch, ji_pitch in zip(
            range(*ZONES[0]), REAL_AVAILABLE_PITCHES_FOR_GONG_ZONE
        )
    }
    midi_note2ji_pitch_mapping_per_zone.update({"gong": midi_pitch2ji_pitch})


MIDI_NOTE2JI_PITCH_PER_ZONE = _generate_keyboard_midi_note2ji_pitch_mapping()
_generate_keyboard_midi_note2ji_pitch_mapping_for_gong_zone(MIDI_NOTE2JI_PITCH_PER_ZONE)


def _generate_keyboard_mapping_files():
    def gen_right_hand_mapping():
        _right_hand_mapping_path = (
            "{}/midi_note2freq_and_instrument_mapping.json".format(KEYBOARD_SETUP_PATH)
        )

        data = {
            midi_note: (
                float(jipitch) * globals_.CONCERT_PITCH,
                globals_.PITCH2INSTRUMENT[jipitch.normalize()],
            )
            for midi_note, jipitch in MIDI_NOTE2JI_PITCH_PER_ZONE["sine"].items()
        }
        with open(_right_hand_mapping_path, "w") as f:
            json.dump(data, f)

    def gen_left_hand_mapping():
        # generate scl file ... kbm file has been written by hand and has to adapted
        # manually in case of any significant change
        scl_f_name = "pteq.scl"
        _left_hand_mapping_path = "{}/{}".format(KEYBOARD_SETUP_PATH, scl_f_name)

        rising_pitches = tuple(sorted(MIDI_NOTE2JI_PITCH_PER_ZONE["pianoteq"].values()))
        first_ct = rising_pitches[0].cents
        cent_values = tuple(p.cents - first_ct for p in rising_pitches[1:]) + (3600,)
        with open(_left_hand_mapping_path, "w") as f:
            f.write(
                "\n".join(
                    (
                        "! {}".format(scl_f_name),
                        "!",
                        " 21 pitches uneven distributed on 3 octaves.",
                        " 36",
                        "!\n",
                    )
                )
            )
            for ct in cent_values:
                f.write("{}\n".format(ct))

    gen_right_hand_mapping()
    gen_left_hand_mapping()


_generate_keyboard_mapping_files()


KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE = {
    zone_name: {
        (
            REAL_GONG_PITCH2SYMBOLIC_GONG_PITCH[ratio] if zone_name == "gong" else ratio
        ): globals_.MIDI_PITCH2ABJAD_PITCH[midi_note]
        for midi_note, ratio in zone.items()
    }
    for zone_name, zone in MIDI_NOTE2JI_PITCH_PER_ZONE.items()
}


# make a general file for saving midi-tone => ji.Pitch
MIDI_NOTE2JI_PITCH_PER_ZONE
with open('{}/midi-note2ji-ratio.json'.format(KEYBOARD_SETUP_PATH), 'w') as f:
    data = {}
    for zone, zone_data in MIDI_NOTE2JI_PITCH_PER_ZONE.items():
        for midi_note, ji_pitch in zone_data.items():
            data.update({int(midi_note): (ji_pitch.numerator, ji_pitch.denominator)})

    json.dump(data, f)


class Keyboard(general.AMLTrack):
    base_shortest_duration = fractions.Fraction(1, 128)
    common_shortest_duration = fractions.Fraction(1, 64)
    shortest_duration_space = 2.5

    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        staves_for_midi_render: abjad.StaffGroup,
        title: str = None,
        resolution: int = None,
    ):
        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"),
            abjad_data[0][0][0],
        )

        for staff in abjad_data[1:]:
            # abjad.attach(
            #     abjad.LilyPondLiteral("\\magnifyStaff #12/14", "before"), staff[0][0]
            # )
            abjad.attach(
                # abjad.LilyPondLiteral("\\accidentalStyle modern-cautionary", "before"),
                abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic-first", "before"),
                staff[0][0],
            )

        abjad_data = abjad.Container(
            [
                abjad.mutate(abjad_data[0]).copy(),
                abjad.StaffGroup([abjad.mutate(d).copy() for d in abjad_data[1:]]),
            ]
        )
        abjad_data.simultaneous = True

        abjad.attach(
            abjad.LilyPondLiteral("\\magnifyStaff #4/7", "before"), abjad_data[0][0][0]
        )
        # abjad.attach(abjad.Clef("treble^8"), abjad_data[1][0][0][0])
        # abjad.attach(abjad.Clef("bass"), abjad_data[1][1][0][0])

        # adapted abjad data that omits the orientation line for midi file creation
        self._midi_abjad_data = abjad.Score(
            [abjad.StaffGroup([abjad.mutate(d).copy() for d in staves_for_midi_render])]
        )

        super().__init__(abjad_data, sound_engine, title, resolution)

    def synthesize(self, name: str) -> subprocess.Popen:
        self.sound_engine.render(name).wait()

    def _make_midi_file_score_block(self):
        score_block = abjad.Block("score")
        midi_block = abjad.Block("midi")
        score_block.items.append(abjad.LilyPondLiteral("\\unfoldRepeats \\articulate "))
        score_block.items.append(self._midi_abjad_data)
        score_block.items.append(midi_block)
        return score_block

    def make_midi_file(self, name: str) -> None:
        lilypond_file = self._make_any_lilypond_file(
            self._make_midi_file_score_block(),
            self.write2png,
            self.global_staff_size,
            self.margin,
            self.format,
            self.lilypond_version,
            includes=["articulate.ly"],
        )
        lily.write_lily_file(lilypond_file, name)
        lily.render_lily_file(name, output_name=name)


class VeryLeftHandKeyboardEngine(synthesis.BasedCsoundEngine):
    # print_output = True
    # remove_files = False

    ji_pitch2index = {
        value: key - LOWEST_MIDI_NOTE
        for key, value in MIDI_NOTE2JI_PITCH_PER_ZONE["gong"].items()
    }

    cname = ".gong"

    kempul_samples_path = "aml/electronics/kempul_samples"
    adapted_kempul_samples_path = "{}/adapted".format(kempul_samples_path)

    kenong_samples_path = "aml/electronics/kenong_samples"
    adapted_kenong_samples_path = "{}/adapted".format(kenong_samples_path)

    def __init__(self, novent_line: lily.NOventLine):
        self._types = []
        for novent in novent_line:
            novent.pitch = [
                SYMBOLIC_GONG_PITCH2REAL_GONG_PITCH[p]
                for p in novent.pitch
                if p.octave == SYMBOLIC_GONG_OCTAVE
            ]

            try:
                tp = ["kenong", "gong"][novent.pedal.status]
            except AttributeError:
                tp = None
                assert not novent.pitch

            self._types.append(tp)

        self._novent_line = novent_line

    @property
    def orc(self) -> str:
        lines = (
            "0dbfs=1",
            "nchnls=1\n",
            "instr 1",
            "asig0, asig1 diskin2 p4, 1",
            "out (asig0 + asig1) * 0.5 * p5",
            "endin\n",
        )
        return "\n".join(lines)

    @property
    def sco(self) -> str:
        lines = []
        for tp, novent in zip(self._types, self._novent_line.convert2absolute()):
            if novent.pitch:
                for pitch in novent.pitch:
                    idx = self.ji_pitch2index[pitch]
                    if tp == "gong":
                        path = self.adapted_kempul_samples_path
                        volume = 1
                    else:
                        path = self.adapted_kenong_samples_path
                        volume = 0.95

                    if novent.volume:
                        volume *= novent.volume

                    path = "{}/{}.wav".format(path, idx)
                    duration = float(pyo.sndinfo(path)[1] + novent.delay)
                    line = 'i1 {} {} "{}" {}'.format(
                        float(novent.delay), duration, path, volume
                    )
                    lines.append(line)

        return "\n".join(lines)


class LeftHandKeyboardEngine(synthesis.PyteqEngine):
    glissando_maker = infit.ActivityLevel(6)
    glissando_size_maker = infit.Uniform(0.1, 0.22)
    glissando_pitch_size_maker = infit.Uniform(-150, 150)

    _sec_delay = 0.001

    def __init__(self, novent_line: lily.NOventLine):
        for novent in novent_line:
            novent.pitch = [p for p in novent.pitch if p.octave != SYMBOLIC_GONG_OCTAVE]
            if next(self.glissando_maker):
                glissando_duration = next(self.glissando_size_maker)
                glissando_size = next(self.glissando_pitch_size_maker)
                novent.glissando = old.GlissandoLine(
                    interpolations.InterpolationLine(
                        [
                            old.PitchInterpolation(
                                glissando_duration, mel.SimplePitch(100, glissando_size)
                            ),
                            old.PitchInterpolation(novent.duration, ji.r(1, 1)),
                            old.PitchInterpolation(0, ji.r(1, 1)),
                        ]
                    )
                )

        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )
        super().__init__(
            # fxp="aml/electronics/saron_only_sound.fxp"
            fxp="aml/electronics/aml_harp.fxp"
            # preset='"Erard Player"'
            # preset='"Concert Harp Daily"'
        )

    @property
    def CONCERT_PITCH(self) -> float:
        return globals_.CONCERT_PITCH

    # def render(self, name: str) -> subprocess.Popen:
    #     return super().render(name, self._novent_line)

    def render(self, name: str) -> subprocess.Popen:
        seq = []
        for chord in self._novent_line:
            dur = float(chord.delay)
            if chord.pitch != mel.TheEmptyPitch and bool(chord.pitch):
                size = len(chord.pitch)
                for idx, pi in enumerate(chord.pitch):
                    if idx + 1 == size:
                        de = float(dur) - (self._sec_delay * idx)
                    else:
                        de = self._sec_delay
                    if pi != mel.TheEmptyPitch:
                        if chord.volume:
                            volume = chord.volume
                        else:
                            volume = self.volume

                        tone = midiplug.PyteqTone(
                            ji.JIPitch(pi, multiply=self.CONCERT_PITCH),
                            de,
                            dur,
                            volume=volume,
                            sustain_pedal=1,
                            glissando=chord.glissando,
                            impedance=random.uniform(2.2, 2.8),
                            q_factor=random.uniform(0.4, 1.4),
                            blooming_energy=random.uniform(0.5, 1.3),
                            blooming_inertia=random.uniform(0.7, 1.7),
                            hammer_noise=random.uniform(1.5, 3),
                        )
                    else:
                        tone = midiplug.PyteqTone(
                            mel.TheEmptyPitch, de, dur, volume=self.volume
                        )
                    seq.append(tone)
            else:
                seq.append(old.Rest(dur))

        pt = midiplug.Pianoteq(tuple(seq), self.available_midi_notes)
        return pt.export2wav(name, 1, self.preset, self.fxp)


class RightHandKeyboardEngine(synthesis.PyoEngine):
    # adapted sine wave generator

    _tail = 0.45  # seconds
    _vol_gen = infit.Uniform(0.5, 0.7)
    _instrument2channel_mapping = {"violin": 0, "viola": 1, "cello": 2}

    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )

    @property
    def duration(self) -> float:
        return float(self._novent_line.duration)

    @property
    def CONCERT_PITCH(self) -> float:
        return globals_.CONCERT_PITCH

    @property
    def instrument(self) -> pyo.EventInstrument:
        tail = self._tail
        vol_gen = self._vol_gen

        class myinstr(pyo.EventInstrument):
            def __init__(self, **args):
                super().__init__(**args)
                fadein, fadeout = 0.6, 0.6
                self.env = pyo.Fader(
                    fadein=fadein, fadeout=fadeout, dur=self.dur + tail,
                )

                # print(self.freqs, self.chnl, self.dur)

                for idx, freq, chnl in zip(
                    range(len(self.freqs)), self.freqs, self.chnl
                ):
                    generator_name = "generator{}".format(idx)
                    setattr(self, generator_name, _right_hand_synth.SineGenerator(freq))
                    # new_mul = self.env * next(vol_gen)
                    # getattr(self, generator_name).generator.mul *= new_mul
                    getattr(self, generator_name).mul = next(vol_gen) * self.vol
                    getattr(self, generator_name).out(dur=self.dur)
                    getattr(self, generator_name).generator.out(chnl)

                self.env.play()

        return myinstr

    def render(self, name: str) -> None:
        globals_.PYO_SERVER = pyo.Server(sr=44100, audio="offline", nchnls=3)
        globals_.PYO_SERVER.boot()
        globals_.PYO_SERVER.recordOptions(
            dur=self.duration + self._tail + 1,
            filename="{}.wav".format(name),
            sampletype=4,
        )
        events = pyo.Events(
            instr=self.instrument,
            freqs=pyo.EventSeq(
                [
                    [float(p) * globals_.CONCERT_PITCH for p in pitch] if pitch else []
                    for pitch in self._novent_line.pitch
                ],
                occurrences=1,
            ),
            dur=pyo.EventSeq([float(d) for d in self._novent_line.delay]),
            vol=pyo.EventSeq(
                [float(vol) if vol else 1 for vol in self._novent_line.volume]
            ),
            chnl=pyo.EventSeq(
                [
                    [
                        self._instrument2channel_mapping[
                            globals_.PITCH2INSTRUMENT[p.normalize()]
                        ]
                        for p in pitch
                    ]
                    if pitch
                    else []
                    for pitch in self._novent_line.pitch
                ],
                occurrences=1,
            ),
            outs=3,
        )
        events.play()
        events.stop(wait=self.duration)
        globals_.PYO_SERVER.start()


class KeyboardSoundEngine(synthesis.SoundEngine):
    def __init__(
        self, right_hand_nline: lily.NOventLine, left_hand_nline: lily.NOventLine
    ):
        self.right_hand_engine = RightHandKeyboardEngine(right_hand_nline)
        self.left_hand_engine = LeftHandKeyboardEngine(left_hand_nline.copy())
        self.very_left_hand_engine = VeryLeftHandKeyboardEngine(left_hand_nline.copy())

    def render(self, name: str) -> None:
        rhn = "{}_right".format(name)
        lhn = "{}_left".format(name)
        vlhn = "{}_very_left".format(name)
        self.right_hand_engine.render(rhn)
        self.very_left_hand_engine.render(vlhn)
        return self.left_hand_engine.render(lhn)


class SilentKeyboardMaker(general.AMLTrackMaker):
    _track_class = Keyboard

    def _prepare_staves(
        self, polyline: old.PolyLine, segment_maker: mus.SegmentMaker
    ) -> old.PolyLine:
        # polyline[1][0].margin_markup = attachments.MarginMarkup(
        #     "{}.{}".format(segment_maker.chapter, segment_maker.verse),
        #     context="StaffGroup",
        # )

        for nol in polyline:
            nol[0].tempo = attachments.Tempo((1, 4), segment_maker.tempo)

        polyline[1][0].clef = attachments.Clef("treble^8")
        polyline[2][0].clef = attachments.Clef("bass")

        return old.PolyLine(polyline)

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        return pl

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return synthesis.SilenceEngine(1)


class KeyboardMaker(SilentKeyboardMaker):
    """Class for the generation of Keyboard track.

    args:
        - colotomic_structure: tuple with as many elements as there are bars
          in the metrical loop. elements can be:
              0: no marker
              1: gong
              2: kenong
    """

    _normalized_unusual_first_pitch = globals_.INTONATIONS_PER_SCALE_DEGREE[0][
        0
    ].normalize()

    def __init__(
        self,
        lh_min_volume: float = 0.52,
        lh_max_volume: float = 0.75,
        lh_min_metricity_to_add_harmony: float = 0.7,
        lh_min_metricity_to_add_restricted_harmony: float = 0.38,
        lh_min_metricity_to_add_accent: float = 0.93,
        lh_max_metricity_for_arpeggio: float = 0.94,
        lh_prohibit_repetitions: bool = True,
        lh_add_repetitions_avoiding_notes: bool = True,
        rh_likelihood_making_harmony: float = 0,
        harmonies_min_difference: float = 250,
        harmonies_max_difference: float = 1200,
        colotomic_structure: tuple = None,
    ):
        self.lh_min_volume = lh_min_volume
        self.lh_vol_difference = lh_max_volume - lh_min_volume
        self.lh_min_metricity_to_add_accent = lh_min_metricity_to_add_accent
        self.lh_min_metricity_to_add_harmony = lh_min_metricity_to_add_harmony
        self.lh_max_metricity_for_arpeggio = lh_max_metricity_for_arpeggio
        self.lh_min_metricity_to_add_restricted_harmony = (
            lh_min_metricity_to_add_restricted_harmony
        )
        self.lh_prohibit_repetitions = lh_prohibit_repetitions
        self.lh_add_repetitions_avoiding_notes = lh_add_repetitions_avoiding_notes
        self.rh_likelihood_making_harmony = rh_likelihood_making_harmony
        self._rh_make_harmony_on_first_beat = infit.Uniform(0, 1)
        self.harmonies_min_difference = harmonies_min_difference
        self.harmonies_max_difference = harmonies_max_difference
        self.colotomic_structure = colotomic_structure

    def __call__(self) -> Keyboard:
        # overwriting default call method to resolve complex problem of having the same
        # ratio mapped to different midi keys depending on the particular staff.

        # 1. make abjad data
        staves = []
        staves_for_midi_render = abjad.StaffGroup([])

        left_hand_keyboard_ratio2abjad_pitch = {}
        left_hand_keyboard_ratio2abjad_pitch.update(
            KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE["pianoteq"]
        )
        left_hand_keyboard_ratio2abjad_pitch.update(
            KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE["gong"]
        )

        # depending on the particular sub-staff the ratio2pitch_class_dict and the
        # respective method how to detect abjad pitches does get adapted
        for line, used_ratio2pitch_class_dict, convertion_method in zip(
            self._prepare_staves(self.musdat, self._segment_maker),
            (
                self.ratio2pitchclass_dict,
                KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE["sine"],
                left_hand_keyboard_ratio2abjad_pitch,
            ),
            (
                None,
                lambda pitch, mapping: mapping[pitch],
                lambda pitch, mapping: mapping[pitch],
            ),
        ):
            activate_accidental_finder = False
            if convertion_method is not None:
                staves_for_midi_render.append(
                    self._convert_novent_line2abjad_staff(
                        line,
                        self.bars,
                        used_ratio2pitch_class_dict,
                        self.repeated_areas,
                        convertion_method,
                        write_true_repetition=True,
                    )
                )
                activate_accidental_finder = False

            staves.append(
                self._convert_novent_line2abjad_staff(
                    line,
                    self.bars,
                    used_ratio2pitch_class_dict,
                    self.repeated_areas,
                    convertion_method,
                    activate_accidental_finder=activate_accidental_finder,
                )
            )

        abjad_data = abjad.Container(staves)
        abjad_data.simultaneous = True

        # 2. generate sound engine
        sound_engine = self.make_sound_engine()

        return self._track_class(
            abjad_data, sound_engine, staves_for_midi_render, title=self.title
        )

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        pl[1] = self._make_right_hand(segment_maker)
        pl[2] = self._make_left_hand(segment_maker)

        return pl

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return KeyboardSoundEngine(
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[1]),
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[2]),
        )

    ###################################################################################
    #           general methods that are used for the algorithms of both hands        #
    ###################################################################################

    @staticmethod
    def _find_harmonies_within_one_octave(
        melodic_pitch: ji.JIPitch,
        available_pitches: tuple,
        max_pitches: int = 4,
        min_difference: float = 250,
        max_difference: float = 1200,
    ) -> tuple:
        available_pitches_within_one_octave = tuple(
            p for p in available_pitches if abs((p - melodic_pitch).cents) < 1200
        )

        if available_pitches_within_one_octave:
            potential_harmonies = []

            for n_pitches in range(
                1, min((max_pitches + 1, len(available_pitches_within_one_octave) + 1))
            ):
                for potential_harmony in itertools.combinations(
                    available_pitches_within_one_octave, n_pitches
                ):
                    potential_harmony += (melodic_pitch,)
                    is_valid = True
                    for p0, p1 in itertools.combinations(potential_harmony, 2):
                        diff = abs((p1 - p0).cents)
                        if diff <= min_difference or diff >= max_difference:
                            is_valid = False
                            break

                    if is_valid:
                        potential_harmonies.append(potential_harmony)

            if potential_harmonies:
                size_per_harmony = tuple(len(h) for h in potential_harmonies)
                max_harmony_size = max(size_per_harmony)
                potential_harmonies = tuple(
                    h
                    for s, h in zip(size_per_harmony, potential_harmonies)
                    if s == max_harmony_size
                )
                harmonies = tuple(potential_harmonies)

            else:
                harmonies = (tuple([]),)

        else:
            harmonies = (tuple([]),)

        return harmonies

    ###################################################################################
    #           functions to generate the musical data for the left hand              #
    ###################################################################################

    @staticmethod
    def _mlh_sort_orientation_note_pitches(
        harmonic_field: dict, available_instruments: tuple
    ) -> tuple:
        if harmonic_field:
            available_pitches = functools.reduce(
                operator.add,
                (
                    globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[name].scale
                    for name in available_instruments
                ),
            )
            pitches_sorted_by_harmonicity = tuple(
                map(
                    operator.itemgetter(0),
                    sorted(
                        (
                            (p, harmonicity)
                            for p, harmonicity in harmonic_field.items()
                            if p.normalize() in available_pitches
                        ),
                        key=operator.itemgetter(1),
                        reverse=True,
                    ),
                )
            )
            pitches_in_sd_3_and_6 = tuple(
                p
                for p in pitches_sorted_by_harmonicity
                if globals_.PITCH2SCALE_DEGREE[p] in (3, 6)
            )

            pitches = tuple(
                p
                for p in pitches_sorted_by_harmonicity
                if p not in pitches_in_sd_3_and_6
            )
            pitches += pitches_in_sd_3_and_6
            return pitches

        else:
            return tuple([])

    @staticmethod
    def _mlh_detect_available_pitch_classes_per_beat(
        segment_maker: mus.SegmentMaker,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        orientation_rhythm_metricity_pairs: tuple,
    ):
        available_pitches_per_mandatory_beat = []
        for data in orientation_rhythm_metricity_pairs:
            absolute_position, metricity = data
            primes = spread_metrical_loop.get_primes_of_absolute_rhythm(
                absolute_position
            )
            slice_idx = segment_maker.bread.find_indices_of_responsible_slices(
                absolute_position, absolute_position + 1
            )[0]
            slice_ = segment_maker.bread[slice_idx]

            available_instruments = tuple(
                spread_metrical_loop.prime_instrument_mapping[prime] for prime in primes
            )
            available_pitches = KeyboardMaker._mlh_sort_orientation_note_pitches(
                slice_.harmonic_field, available_instruments
            )
            available_pitches_per_mandatory_beat.append(available_pitches)

        return tuple(available_pitches_per_mandatory_beat)

    @classmethod
    def _mlh_detect_absolute_scale_degree(
        cls, pitch: ji.JIPitch, relative_ground_octave: int
    ) -> int:
        normalized_pitch = pitch.normalize()
        relative_scale_degree = globals_.PITCH2SCALE_DEGREE[normalized_pitch]
        pitch_octave = pitch.octave

        # remove error occuring from weird intonation for first scale degree where
        # octave is returning a false value
        if normalized_pitch == cls._normalized_unusual_first_pitch:
            pitch_octave += 1

        absolute_scale_degree = relative_scale_degree + (
            (pitch.octave - relative_ground_octave) * 7
        )
        return int(absolute_scale_degree)

    @classmethod
    def _mlh_detect_absolute_scale_degrees(
        cls, pitch0: ji.JIPitch, pitch1: ji.JIPitch
    ) -> tuple:

        p0_normalized, p1_normalized = pitch0.normalize(), pitch1.normalize()

        scale_degrees = tuple(
            globals_.PITCH2SCALE_DEGREE[p] for p in (p0_normalized, p1_normalized)
        )

        octaves = [p.octave for p in (pitch0, pitch1)]

        # remove error occuring from weird intonation for first scale degree where
        # octave is returning a false value
        for idx, p in enumerate((p0_normalized, p1_normalized)):
            if p == cls._normalized_unusual_first_pitch:
                octaves[idx] += 1

        min_oct = min(octaves)
        octaves = [oc - min_oct for oc in octaves]
        absolute_scale_degrees = tuple(
            sd + (oc * 7) for sd, oc in zip(scale_degrees, octaves)
        )

        return absolute_scale_degrees, min_oct

    def _mlh_make_melodic_core(
        self,
        start_pitch: ji.JIPitch,
        segment_maker: mus.SegmentMaker,
        orientation_rhythm_metricity_pairs: tuple,
        available_pitches_per_mandatory_beat: tuple,
    ) -> tuple:
        """Return musical_data: tuple, scale_degrees_distances: tuple, fitness_value: int

        musical_data is composed of subtuples where each subtuple contains:
            (absolute_position: float, pitch: ji.JIPitch, relative_metricity: float)
        """

        musical_data = [
            (
                orientation_rhythm_metricity_pairs[0][0],
                start_pitch,
                orientation_rhythm_metricity_pairs[0][1],
            )
        ]
        scale_degrees_distances = []

        fitness = 0
        for available_pitches, rhythmical_data in zip(
            available_pitches_per_mandatory_beat[1:],
            orientation_rhythm_metricity_pairs[1:],
        ):
            last_pitch = musical_data[-1][1]
            absolute_position, metricity = rhythmical_data
            if self.lh_prohibit_repetitions:
                octave_ignoring_last_pitch = last_pitch.set_val_border(2)
                filtered_available_pitches = tuple(
                    pitch
                    for pitch in available_pitches
                    if pitch.set_val_border(2) != octave_ignoring_last_pitch
                )
            else:
                filtered_available_pitches = tuple(available_pitches)
            if not filtered_available_pitches:
                filtered_available_pitches = tuple(available_pitches)

            filtered_available_pitches = sorted(filtered_available_pitches)
            closest_pitch = tools.find_closest_item(
                last_pitch, filtered_available_pitches
            )

            musical_data.append((absolute_position, closest_pitch, metricity))

            # detect distance in scale degrees
            scale_degrees, _ = type(self)._mlh_detect_absolute_scale_degrees(
                last_pitch, closest_pitch
            )

            scale_degrees_distance = scale_degrees[1] - scale_degrees[0]

            # melodic jumps within the same octave that omit auxiliary pitches 3 or 6 are
            # read as having only one scale degree difference. therefore melodic phrases
            # that stay within the global pentatonic are accepted.
            if set(scale_degrees) in (set([7, 5]), set([2, 4])):
                if scale_degrees_distance > 0:
                    scale_degrees_distance -= 1
                else:
                    scale_degrees_distance += 1

            fitness += abs(scale_degrees_distance)
            scale_degrees_distances.append(scale_degrees_distance)

        return tuple(musical_data), tuple(scale_degrees_distances), fitness

    def _mlh_detect_melodic_core(
        self,
        segment_maker: mus.SegmentMaker,
        orientation_rhythm_metricity_pairs: tuple,
        available_pitches_per_mandatory_beat: tuple,
    ) -> tuple:
        """Return (musical_data: tuple, scale_degrees_distances: tuple)

        musical_data is composed of subtuples where each subtuple contains:
            (absolute_position: float, pitch: ji.JIPitch, relative_metricity: float)
        """

        # loop through all different first - pitch options, generate a melodic core and
        # save its fitness value
        hof = crosstrainer.Stack(size=1)
        for potential_first_pitch in available_pitches_per_mandatory_beat[0]:
            (
                melodic_core,
                scale_degrees_distances,
                fitness,
            ) = self._mlh_make_melodic_core(
                potential_first_pitch,
                segment_maker,
                orientation_rhythm_metricity_pairs,
                available_pitches_per_mandatory_beat,
            )
            hof.append((melodic_core, scale_degrees_distances), fitness)

        return hof.best[0]

    @staticmethod
    def _mlh_make_optional_some_pitches_attachment(
        melodic_pitch: ji.JIPitch, pitches: tuple
    ) -> attachments.OptionalSomePitches:
        none_melodic_pitch_positions = tuple(
            idx for idx, pitch in enumerate(pitches) if pitch != melodic_pitch
        )
        return attachments.OptionalSomePitches(none_melodic_pitch_positions)

    @staticmethod
    def _mlh_make_arpeggio_depending_on_melodic_pitch(
        harmony: tuple, melodic_pitch: ji.JIPitch
    ) -> attachments.Arpeggio:
        sorted_harmony = sorted(harmony)
        n_pitches = len(harmony)
        pposition = sorted_harmony.index(melodic_pitch)

        if pposition < n_pitches / 2:
            direction = abjad.enums.Down
        else:
            direction = abjad.enums.Up

        return attachments.Arpeggio(direction)

    def _mlh_detect_adapted_event_data_depending_on_metricity(
        self, melodic_pitch: ji.JIPitch, harmony: tuple, metricity: float
    ):
        volume = self.lh_min_volume + (self.lh_vol_difference * metricity)
        pitches = [melodic_pitch]
        attachments_ = dict([])

        if metricity > self.lh_min_metricity_to_add_accent:
            attachments_.update(
                {"articulation_once": attachments.ArticulationOnce("accent")}
            )

        if metricity > self.lh_min_metricity_to_add_harmony:
            if harmony:
                pitches = list(harmony)

        elif metricity > self.lh_min_metricity_to_add_restricted_harmony:
            if harmony:
                pitches = sorted(harmony)
                if len(pitches) == 2:
                    osp_attachment = self._mlh_make_optional_some_pitches_attachment(
                        melodic_pitch, pitches
                    )
                    attachments_.update({"optional_some_pitches": osp_attachment})
                else:
                    attachments_.update({"choose": attachments.Choose()})

        if metricity < self.lh_max_metricity_for_arpeggio and len(pitches) > 1:
            attachments_.update(
                {
                    "arpeggio": self._mlh_make_arpeggio_depending_on_melodic_pitch(
                        pitches, melodic_pitch
                    )
                }
            )

        return pitches, volume, attachments_

    def _mlh_adapt_melodic_core(
        self, melodic_core: tuple, available_pitches_per_mandatory_beat: tuple
    ) -> tuple:
        """Return tuple that contain subtuples.

        Each subtuple contains:
            (absolute_position: float, pitch: list, volume: float, attachments: dict)
        """
        adapted_melodic_core = []
        for idx, event, available_pitches in zip(
            range(len(melodic_core)), melodic_core, available_pitches_per_mandatory_beat
        ):
            start, melodic_pitch, metricity = event

            normalized_melodic_pitch = melodic_pitch.normalize()

            if idx > 0:
                previous_event = adapted_melodic_core[idx - 1]
                prohibited_pitches = list(previous_event[1])
            else:
                prohibited_pitches = []

            try:
                prohibited_pitches.append(melodic_core[idx + 1][1])
            except IndexError:
                # if the current event is the last event no next event exists. this can be
                # ignored.
                pass

            available_pitches = tuple(
                p
                for p in available_pitches
                if p.normalize() != normalized_melodic_pitch
                and p not in prohibited_pitches
            )

            harmony = self._find_harmonies_within_one_octave(
                melodic_pitch, available_pitches, 4
            )[0]

            (
                pitches,
                volume,
                attachments_,
            ) = self._mlh_detect_adapted_event_data_depending_on_metricity(
                melodic_pitch, harmony, metricity
            )

            attachments_.update({"pedal": attachments.Pedal(False)})

            adapted_melodic_core.append((start, pitches, volume, attachments_))

        return tuple(adapted_melodic_core)

    @staticmethod
    def _mlh_find_available_positions_and_pitches_in_between(
        range_: tuple,
        segment_maker: mus.SegmentMaker,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        available_pitches_for_left_hand: tuple,
    ) -> tuple:
        """Return tuple filled with subtuples of the form (position, metricity, pitches)"""
        rm_pairs = spread_metrical_loop.get_all_rhythm_metricitiy_pairs(*range_)[1:]
        apc_per_beat = KeyboardMaker._mlh_detect_available_pitch_classes_per_beat(
            segment_maker, spread_metrical_loop, rm_pairs
        )
        ap_per_beat = tuple(
            tuple(
                pitch
                for pitch in available_pitches_for_left_hand
                if pitch.normalize() in available_pitch_classes
            )
            for available_pitch_classes in apc_per_beat
        )
        return tuple(
            rmp + (pitches,) for rmp, pitches in zip(rm_pairs, ap_per_beat) if pitches
        )

    def _mlh_smooth_melody(
        self,
        event0: tuple,
        event1: tuple,
        data_per_available_beat: tuple,
        n_scale_degrees_distance: int,
        melodic_pitches_scale_degrees: tuple,
        relative_ground_octave: int,
    ) -> tuple:
        additional_events = []

        # add absolute scale degrees to the pitch information in each beat.
        # And filter only those beats that contain pitches whose absolute scale
        # degrees are in between the scale degrees of the framing melodic pitches.
        filtered_data_per_available_beat = []
        for data in data_per_available_beat:
            rhythmical_data = data[:2]
            pitches = data[-1]
            new_pitches = []
            for pitch in pitches:
                absolute_scale_degree = type(self)._mlh_detect_absolute_scale_degree(
                    pitch, relative_ground_octave
                )
                is_valid = (
                    absolute_scale_degree > melodic_pitches_scale_degrees[0],
                    absolute_scale_degree < melodic_pitches_scale_degrees[1],
                )
                if all(is_valid):
                    new_pitches.append((pitch, absolute_scale_degree))

            if new_pitches:
                filtered_data_per_available_beat.append(
                    rhythmical_data + (tuple(new_pitches),)
                )

        # only continue if there are any chances to make melodic interpolations
        if filtered_data_per_available_beat:

            direction_of_melodic_movement = n_scale_degrees_distance > 0

            # try to find the best solution now where "best" is defined as the
            # solution that results in the averagely smallest melodic steps. if
            # two solutions may have equally small steps, the solution that
            # results in higher metricity is prefered.
            solutions = []
            for n_added_optional_interpolation_events in range(
                1, len(filtered_data_per_available_beat) + 1
            ):
                for choosen_interpolation_events in itertools.combinations(
                    filtered_data_per_available_beat,
                    n_added_optional_interpolation_events,
                ):
                    # making sure the events are sorted in correct time order
                    choosen_interpolation_events = sorted(
                        choosen_interpolation_events, key=operator.itemgetter(0)
                    )
                    available_pitches_per_choosen_interpolation_event = tuple(
                        map(operator.itemgetter(2), choosen_interpolation_events)
                    )

                    for pitches_per_choosen_interpolation_event in itertools.product(
                        *available_pitches_per_choosen_interpolation_event
                    ):
                        absolute_scale_degrees_per_pitch = tuple(
                            map(
                                operator.itemgetter(1),
                                pitches_per_choosen_interpolation_event,
                            )
                        )
                        n_scale_degrees_difference_between_pitches = tuple(
                            b - a
                            for a, b in zip(
                                (melodic_pitches_scale_degrees[0],)
                                + absolute_scale_degrees_per_pitch,
                                absolute_scale_degrees_per_pitch
                                + (melodic_pitches_scale_degrees[1],),
                            )
                        )

                        is_addable = (
                            0 not in n_scale_degrees_difference_between_pitches,
                            all(
                                tuple(
                                    (n_scale_degrees_distance > 0)
                                    == direction_of_melodic_movement
                                    for n_scale_degrees_distance in n_scale_degrees_difference_between_pitches
                                )
                            ),
                        )

                        if all(is_addable):
                            fitness = sum(
                                n_scale_degrees_difference_between_pitches
                            ) / len(n_scale_degrees_difference_between_pitches)
                            actual_pitches_per_interpolation_event = tuple(
                                map(
                                    operator.itemgetter(0),
                                    pitches_per_choosen_interpolation_event,
                                )
                            )

                            solution = tuple(
                                interpolation_event[:2] + (interpolation_pitch,)
                                for interpolation_event, interpolation_pitch in zip(
                                    choosen_interpolation_events,
                                    actual_pitches_per_interpolation_event,
                                )
                            )
                            solutions.append((solution, fitness))

            if solutions:
                min_fitness = min(solutions, key=operator.itemgetter(1))[1]
                solutions = tuple(
                    solution[0] for solution in solutions if solution[1] == min_fitness
                )
                best_solution = max(
                    solutions, key=lambda solution: sum(event[1] for event in solution),
                )

                for event in best_solution:
                    start_position, _, pitch = event
                    pitches = [pitch]
                    volume = 0.48
                    attachments_ = {"optional": attachments.Optional()}
                    additional_events.append(
                        (start_position, pitches, volume, attachments_)
                    )

        return tuple(additional_events)

    def _mlh_extend_melodic_core(
        self,
        melodic_core: tuple,
        adapted_melodic_core: tuple,
        scale_degrees_distances: tuple,
        segment_maker: mus.SegmentMaker,
        spread_metrical_loop: complex_meters.SpreadMetricalLoop,
        available_pitches_for_left_hand: tuple,
    ) -> tuple:
        """Return tuple that contain subtuples.

        Each subtuple contains:
            (absolute_position: float, pitch: list, volume: float, attachments: dict)
        """

        further_adapted_melodic_core = []
        for (
            adapted_event0,
            adapted_event1,
            event0,
            event1,
            n_scale_degrees_distance,
        ) in zip(
            adapted_melodic_core,
            adapted_melodic_core[1:],
            melodic_core,
            melodic_core[1:],
            scale_degrees_distances,
        ):
            further_adapted_melodic_core.append(adapted_event0)

            tests_if_optional_interpolation_pitches_shall_be_added = (
                n_scale_degrees_distance > 1,
                event0[1] == event1[1],
            )

            if any(tests_if_optional_interpolation_pitches_shall_be_added):
                dpab = KeyboardMaker._mlh_find_available_positions_and_pitches_in_between(
                    (event0[0], event1[0]),
                    segment_maker,
                    spread_metrical_loop,
                    available_pitches_for_left_hand,
                )
                data_per_available_beat = dpab

                pitch0, pitch1 = event0[1], event1[1]
                melodic_pitches_scale_degrees, relative_ground_octave = type(
                    self
                )._mlh_detect_absolute_scale_degrees(pitch0, pitch1)

            # try to add more optional interpolation pitches to potentially smooth the
            # resulting melodic line.
            if tests_if_optional_interpolation_pitches_shall_be_added[0]:
                further_adapted_melodic_core.extend(
                    self._mlh_smooth_melody(
                        event0,
                        event1,
                        data_per_available_beat,
                        n_scale_degrees_distance,
                        melodic_pitches_scale_degrees,
                        relative_ground_octave,
                    )
                )

            # try to add one interpolation pitch to potentially avoid melodic pitch
            # repetition
            elif (
                self.lh_add_repetitions_avoiding_notes
                and tests_if_optional_interpolation_pitches_shall_be_added[1]
            ):
                adapted_data_per_available_beat = []
                for data in data_per_available_beat:
                    rhythmical_data = data[:2]
                    pitches = data[-1]

                    new_pitches = []
                    for pitch in pitches:
                        absolute_scale_degree = type(
                            self
                        )._mlh_detect_absolute_scale_degree(
                            pitch, relative_ground_octave
                        )
                        if absolute_scale_degree not in melodic_pitches_scale_degrees:
                            new_pitches.append((pitch, absolute_scale_degree))

                    adapted_data_per_available_beat.append(
                        rhythmical_data + (tuple(new_pitches),)
                    )

                scale_degrees_distance_per_pitch_per_event = tuple(
                    tuple(
                        abs(
                            pitch_and_abs_scale_degree[1]
                            - melodic_pitches_scale_degrees[0]
                        )
                        for pitch_and_abs_scale_degree in event[2]
                    )
                    for event in adapted_data_per_available_beat
                )
                if scale_degrees_distance_per_pitch_per_event:
                    closest_scale_degree_distance = min(
                        min(
                            scale_degrees_distance_per_pitch_per_event,
                            key=lambda scale_degrees_distance_per_pitch: min(
                                scale_degrees_distance_per_pitch
                            ),
                        )
                    )

                    filtered_data_per_available_beat = []
                    for data, scale_degrees_distance_per_pitch in zip(
                        adapted_data_per_available_beat,
                        scale_degrees_distance_per_pitch_per_event,
                    ):
                        rhythmical_data = data[:2]
                        pitches = data[-1]
                        pitches = tuple(
                            p[0]
                            for p, sdd in zip(pitches, scale_degrees_distance_per_pitch)
                            if sdd == closest_scale_degree_distance
                        )
                        if pitches:
                            # arbitrary decision which pitch to choose since those that
                            # are remaining now are all close enough to the repating pitch
                            choosen_pitch = pitches[0]
                            filtered_data_per_available_beat.append(
                                rhythmical_data + (choosen_pitch,)
                            )

                    event = max(
                        filtered_data_per_available_beat, key=operator.itemgetter(1)
                    )
                    start_position, _, pitch = event
                    pitches = [pitch]
                    volume = 0.45
                    attachments_ = {
                        # "optional": attachments.Optional(),
                        "articulation_once": attachments.ArticulationOnce("."),
                    }
                    further_adapted_melodic_core.append(
                        (start_position, pitches, volume, attachments_)
                    )

        further_adapted_melodic_core.append(adapted_melodic_core[-1])

        return tuple(further_adapted_melodic_core)

    def _mlh_append_gong2melodic_data(
        self, left_hand_melodic_data: tuple, segment_maker
    ) -> tuple:
        if self.colotomic_structure:
            colotomic_structure = self.colotomic_structure
            assert (
                len(colotomic_structure)
                == segment_maker.transcription.spread_metrical_loop.loop_size
            )
        else:
            colotomic_structure = [
                0
                for _ in range(
                    segment_maker.transcription.spread_metrical_loop.loop_size
                )
            ]
            colotomic_structure[0] = 1
            colotomic_structure = tuple(colotomic_structure)

        available_gong_pitches = tuple(MIDI_NOTE2JI_PITCH_PER_ZONE["gong"].values())
        absolute_bar_positions = tools.accumulate_from_zero(
            tuple(float(b.duration) for b in segment_maker.bars)
        )[:-1]

        left_hand_melodic_data = list(
            map(lambda sub: list(sub), left_hand_melodic_data)
        )

        for gong_type, absolute_bar_position in zip(
            itertools.cycle(colotomic_structure), absolute_bar_positions
        ):
            if gong_type:
                slice_ = segment_maker.bread.find_responsible_slices(
                    absolute_bar_position, absolute_bar_position + 1
                )[0]
                if slice_.harmonic_field:
                    available_pitches = tuple(
                        p
                        for p in available_gong_pitches
                        if p.normalize() in slice_.harmonic_field
                    )
                    available_pitches = sorted(
                        available_pitches,
                        key=lambda pitch: slice_.harmonic_field[pitch.normalize()],
                        reverse=True,
                    )
                    normalized_available_pitches = tuple(
                        p.normalize() for p in available_pitches
                    )
                    if available_pitches:
                        harmonic_pc = None
                        melodic_pc = None
                        if (
                            slice_.harmonic_pitch
                            and slice_.harmonic_pitch.normalize()
                            in normalized_available_pitches
                        ):
                            harmonic_pc = slice_.harmonic_pitch.normalize()

                        if (
                            slice_.melody_pitch.normalize()
                            in normalized_available_pitches
                        ):
                            melodic_pc = slice_.melody_pitch.normalize()

                        if gong_type == 1:
                            if melodic_pc:
                                choosen_pc = melodic_pc
                            elif harmonic_pc:
                                choosen_pc = harmonic_pc
                            else:
                                choosen_pc = normalized_available_pitches[0]

                            volume = 0.7

                        else:
                            if harmonic_pc:
                                choosen_pc = harmonic_pc
                            elif melodic_pc:
                                choosen_pc = melodic_pc
                            else:
                                choosen_pc = normalized_available_pitches[0]

                            volume = 1

                        choosen_pitch = available_pitches[
                            normalized_available_pitches.index(choosen_pc)
                        ]
                        symbolic_pitch = REAL_GONG_PITCH2SYMBOLIC_GONG_PITCH[
                            choosen_pitch
                        ]
                        item = tuple(
                            idx
                            for idx, sub in enumerate(left_hand_melodic_data)
                            if sub[0] == absolute_bar_position
                        )

                        if item:
                            idx = item[0]
                            left_hand_melodic_data[idx][1].append(symbolic_pitch)
                            left_hand_melodic_data[idx][-2] = volume
                            left_hand_melodic_data[idx][-1].update(
                                {
                                    "arpeggio": attachments.Arpeggio(
                                        direction=abjad.enums.Up
                                    ),
                                    "pedal": attachments.Pedal(gong_type == 1),
                                }
                            )
                        else:
                            left_hand_melodic_data.append(
                                (
                                    absolute_bar_position,
                                    [symbolic_pitch],
                                    volume,
                                    {
                                        "ottava": attachments.Ottava(-1),
                                        "pedal": attachments.Pedal(gong_type == 1),
                                    },
                                )
                            )

        return tuple(
            sorted(
                map(lambda sub: tuple(sub), left_hand_melodic_data),
                key=operator.itemgetter(0),
            ),
        )

    def _mlh_make_nline(self, left_hand_melodic_data: tuple, segment_maker) -> tuple:
        max_duration = 1

        nset = lily.NOventSet(size=segment_maker.duration)
        for current_event, next_event in zip(
            left_hand_melodic_data,
            left_hand_melodic_data[1:] + ((segment_maker.duration, None, None, None),),
        ):
            stop = next_event[0]
            delay = next_event[0] - current_event[0]
            if delay > max_duration:
                stop = current_event[0] + max_duration

            novent = lily.NOvent(
                pitch=current_event[1],
                volume=current_event[2],
                delay=current_event[0],
                duration=stop,
            )
            for key, value in current_event[3].items():
                setattr(novent, key, value)

            if "ottava" not in current_event[3]:
                novent.ottava = attachments.Ottava(0)

            nset.append(novent)

        return nset.novent_line

    def _make_left_hand(self, segment_maker: mus.SegmentMaker) -> lily.NOventLine:
        # (0) find positions where notes shall be added & detect their metrical potential.
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop
        rhythm_metricity_pairs = spread_metrical_loop.get_all_rhythm_metricitiy_pairs()
        orientation_rhythm_metricity_pairs = tuple(
            rhythm_metricity_pairs[idx]
            for idx in segment_maker.rhythmic_orientation_indices
        )
        orientation_metricities = tuple(
            map(operator.itemgetter(1), orientation_rhythm_metricity_pairs)
        )
        sorted_orientation_metricities = sorted(set(orientation_metricities))
        n_sorted_orientation_metricities = len(sorted_orientation_metricities)
        scaled_orientation_metricities = tuple(
            sorted_orientation_metricities.index(metricity)
            / n_sorted_orientation_metricities
            for metricity in orientation_metricities
        )

        orientation_rhythm_metricity_pairs = tuple(
            (rm_pair[0], scaled_metricity)
            for rm_pair, scaled_metricity in zip(
                orientation_rhythm_metricity_pairs, scaled_orientation_metricities
            )
        )

        available_pitches_for_left_hand = tuple(
            KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE["pianoteq"].keys()
        )

        # available pitch classes per mandatory beat
        apc_per_mandatory_beat = self._mlh_detect_available_pitch_classes_per_beat(
            segment_maker, spread_metrical_loop, orientation_rhythm_metricity_pairs
        )

        ap_per_mandatory_beat = tuple(
            tuple(
                pitch
                for pitch in available_pitches_for_left_hand
                if pitch.normalize() in available_pitch_classes
            )
            for available_pitch_classes in apc_per_mandatory_beat
        )

        # (1) find melodic core where each mandatory beat is connected with a particular
        # pitch
        melodic_core, scale_degrees_distances = self._mlh_detect_melodic_core(
            segment_maker, orientation_rhythm_metricity_pairs, ap_per_mandatory_beat,
        )

        # (2) adapt single events of melodic core through adding pitches or playing
        # techniques to events regarding their metricity
        adapted_melodic_core = self._mlh_adapt_melodic_core(
            melodic_core, ap_per_mandatory_beat
        )

        # (3) find optional interpolation tones between mandatory melodic events
        left_hand_melodic_data = self._mlh_extend_melodic_core(
            melodic_core,
            adapted_melodic_core,
            scale_degrees_distances,
            segment_maker,
            spread_metrical_loop,
            available_pitches_for_left_hand,
        )

        # (4) append gong to mark metrical loops
        left_hand_melodic_data = self._mlh_append_gong2melodic_data(
            left_hand_melodic_data, segment_maker
        )

        # (5) combine data to final result: NOventLine
        nline = self._mlh_make_nline(left_hand_melodic_data, segment_maker)

        # remove staccato for events that are longer than 1/8 note
        for novent in nline:

            if novent.articulation_once:

                tests_for_removing_staccato = (
                    novent.articulation_once.abjad
                    == attachments.ArticulationOnce(".").abjad,
                    novent.delay > fractions.Fraction(1, 8),
                )

                if all(tests_for_removing_staccato):
                    novent.articulation_once = None

        return nline

    ###################################################################################
    #           functions to generate the musical data for the right hand             #
    ###################################################################################

    @staticmethod
    def _mrh_detect_available_pitches_on_particular_position(
        position: fractions.Fraction, segment_maker: mus.SegmentMaker
    ) -> tuple:
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop
        available_primes = spread_metrical_loop.get_primes_of_absolute_rhythm(position)
        available_instruments = tuple(
            spread_metrical_loop.prime_instrument_mapping[p] for p in available_primes
        )
        allowed_pitches = tuple(
            map(
                lambda p: p.normalize(),
                functools.reduce(
                    operator.add,
                    tuple(
                        globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[
                            instr
                        ].available_pitches
                        for instr in available_instruments
                    ),
                ),
            )
        )
        slice_ = segment_maker.bread.find_responsible_slices(position, position + 1)[0]
        if slice_.harmonic_field:
            harmonic_field = tuple(
                p for p in slice_.harmonic_field.keys() if p in allowed_pitches
            )
        else:
            harmonic_field = tuple([])
        return tuple(sorted(harmonic_field)), slice_

    def _make_right_hand(self, segment_maker: mus.SegmentMaker) -> lily.NOventLine:
        nset = lily.NOventSet(size=segment_maker.duration)

        available_pitches_for_right_hand = tuple(
            KEYBOARD_RATIO2ABJAD_PITCH_PER_ZONE["sine"].keys()
        )
        for area in segment_maker.areas:
            if not area.pitch.is_empty:
                current_pitch = area.pitch
                octave_ignoring_current_pitch = current_pitch.set_val_border(2)
                pitches_to_choose_from = sorted(
                    p
                    for p in available_pitches_for_right_hand
                    if p.set_val_border(2) == octave_ignoring_current_pitch
                )
                closest_pitch = tools.find_closest_item(
                    current_pitch, pitches_to_choose_from
                )

                if current_pitch.octave == 0 and closest_pitch != current_pitch:
                    closest_pitch = pitches_to_choose_from[-1]

                for event_idx, event in enumerate(area.sine_events):
                    start, stop, event_type = event
                    novent = lily.NOvent(
                        pitch=[closest_pitch], delay=start, duration=stop
                    )

                    if (
                        event_idx > 0
                        or next(self._rh_make_harmony_on_first_beat)
                        < self.rh_likelihood_making_harmony
                    ):
                        # available pitches and slice
                        data = self._mrh_detect_available_pitches_on_particular_position(
                            start, segment_maker
                        )
                        ap, slice_ = data

                        ap = tuple(
                            p
                            for p in available_pitches_for_right_hand
                            if p.normalize() in ap
                        )

                        potential_harmonies = sorted(
                            self._find_harmonies_within_one_octave(
                                closest_pitch,
                                ap,
                                max_pitches=3,
                                min_difference=self.harmonies_min_difference,
                                max_difference=self.harmonies_max_difference,
                            )
                        )

                        # check if any of the potential harmonies has the harmonic_pitch
                        # of the slice and if so filter those out that don't have it
                        normalized_harmonic_pitch = None

                        if slice_.harmonic_pitch:
                            normalized_harmonic_pitch = (
                                slice_.harmonic_pitch.normalize()
                            )

                        if normalized_harmonic_pitch:
                            normalized_potential_harmonies = tuple(
                                tuple(p.normalize() for p in har)
                                for har in potential_harmonies
                            )
                            has_harmonic_pitch = tuple(
                                normalized_harmonic_pitch in normalized_harmony
                                for normalized_harmony in normalized_potential_harmonies
                            )
                            if any(has_harmonic_pitch):
                                potential_harmonies = tuple(
                                    filter(
                                        lambda harmony: has_harmonic_pitch[
                                            potential_harmonies.index(harmony)
                                        ],
                                        potential_harmonies,
                                    )
                                )

                        harmony = sorted(potential_harmonies[0])

                        if harmony:

                            novent.pitch = harmony
                            optional_pitches_indices = tuple(
                                idx
                                for idx, pitch in enumerate(harmony)
                                if pitch != closest_pitch
                                and pitch.normalize() != normalized_harmonic_pitch
                            )
                            if optional_pitches_indices:
                                attachment = attachments.OptionalSomePitches(
                                    optional_pitches_indices
                                )
                                novent.optional_some_pitches = attachment

                    nset.append(novent)

        return nset.novent_line
