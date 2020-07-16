import copy
import functools
import itertools
import operator
import os
import json
import pickle
import uuid

import abjad
import quicktions as fractions
import pyo

from mu.mel import ji
from mu.sco import old
from mu.utils import infit
from mu.utils import tools

from mutools import attachments
from mutools import lily
from mutools import mus
from mutools import synthesis

from aml import areas
from aml import breads
from aml import globals_
from aml import transcriptions
from aml.trackmaker import keyboard
from aml.trackmaker import strings


class _MIXVerse(synthesis.BasedCsoundEngine):
    # remove_files = False
    # print_output = True

    cname = ".mix_verse"
    tail = 0.95

    def __init__(self, sf_path_meta_track_pairs: dict):
        self.sf_path_meta_track_pairs = sf_path_meta_track_pairs
        durations = []
        channels_per_meta_track = {}
        for meta_track, sf_path_meta_track_pair in sf_path_meta_track_pairs.items():
            if meta_track != "keyboard":
                sf_path, _ = sf_path_meta_track_pair
                info = pyo.sndinfo("{}.wav".format(sf_path))
                duration, nchannels = info[1], info[3]
                durations.append(duration)
                channels_per_meta_track.update({meta_track: nchannels})

        self.duration = max(durations) + self.tail

    @staticmethod
    def _mk_basic_instrument() -> tuple:
        summed = "asig = asig0 * p5"
        outs = "outs asig * p6, asig * p7"
        return (
            "instr 1",
            "asig0 diskin2 p4, 1, 0, 0, 6, 4",
            summed,
            outs,
            "endin\n",
        )

    def _mk_keyboard_instrument(self) -> tuple:
        out_left = "(asig0 * p5 * {}) + (asig1 * p5 * {}) + (asig2 * p5 * {})".format(
            *tuple(
                self.sf_path_meta_track_pairs[instr][1].volume_left
                for instr in ("violin", "viola", "cello")
            )
        )
        out_right = "(asig0 * p5 * {}) + (asig1 * p5 * {}) + (asig2 * p5 * {})".format(
            *tuple(
                self.sf_path_meta_track_pairs[instr][1].volume_right
                for instr in ("violin", "viola", "cello")
            )
        )
        outs = "outs {}, {}".format(out_left, out_right)
        return (
            "instr 2",
            "asig0, asig1, asig2 diskin2 p4, 1, 0, 0, 6, 4",
            outs,
            "endin",
        )

    @property
    def orc(self) -> str:
        lines = ["0dbfs=1", "nchnls=2\n"]
        lines.extend(self._mk_basic_instrument())
        lines.extend(self._mk_keyboard_instrument())

        return "\n".join(lines)

    @property
    def sco(self) -> str:
        lines = []
        for (
            meta_track,
            sf_path_meta_track_pair,
        ) in self.sf_path_meta_track_pairs.items():
            path = sf_path_meta_track_pair[0]
            if meta_track == "keyboard":
                path = "{}_left".format(path)

            path = "{}.wav".format(path)

            lines.append(
                'i1 0 {} "{}" {} {} {}'.format(
                    float(self.duration),
                    path,
                    sf_path_meta_track_pair[1].volume,
                    sf_path_meta_track_pair[1].volume_left,
                    sf_path_meta_track_pair[1].volume_right,
                )
            )

        lines.append(
            'i2 0 {} "{}" 0.4'.format(
                float(self.duration),
                "{}_right.wav".format(self.sf_path_meta_track_pairs["keyboard"][0]),
            )
        )
        return "\n".join(lines)


class Verse(mus.Segment):
    def synthesize(self, path: str, sf_name: str, render_each_track: bool = True) -> None:
        sf_path_meta_track_pairs = {}
        for meta_track in globals_.ORCHESTRATION:
            instrument_path = "{}/{}".format(path, meta_track)
            sf_path = "{}/{}".format(instrument_path, sf_name)
            tools.igmkdir(instrument_path)
            track = getattr(self, meta_track)
            if render_each_track:
                process = track.synthesize(sf_path)
                try:
                    process.wait()
                except AttributeError:
                    pass
            sf_path_meta_track_pairs.update(
                {meta_track: (sf_path, globals_.ORCHESTRATION[meta_track])}
            )

        engine = _MIXVerse(sf_path_meta_track_pairs)
        engine.render("{}/mixed".format(path))

    @property
    def score(self) -> abjad.Score:
        # removing orientation lines in all-instruments-score
        sco = abjad.Score([])
        for track_name in self.orchestration:
            if track_name == "keyboard":
                abjad_data = abjad.mutate(getattr(self, track_name).abjad).copy()[-1]
            else:
                abjad_data = abjad.mutate(getattr(self, track_name).abjad).copy()[1]
            sco.append(abjad_data)
        return sco


class VerseMaker(mus.SegmentMaker):
    """Class for the generation of musical segments based on the qiroah transcription.

    Apart from obvious decisions during initalisation like which chapter and which verse
    shall be transcripted, further parameters can be tweaked to influence the resulting
    musical structure.

    Those tweakable parameters include:

        - use_full_scale: (True, False) = False
            if True all 7 pelog pitches will be used for the transcription, but if set
            to False the algorithm will only use those 5 pitch degrees that belong to
            'pelog nem'

        - harmonic_tolerance: (0 - 1) = 0.5
            a very high harmonic tolerance won't add any additional harmonic pitches,
            while a very low tolerance will try to add as many additional harmonic pitches
            as possible.

        - ro_temperature: (0 - 1) = 0.7
            a low temperature increases the chance for a beat to get added to the
            rhythmical orientation line.

        - ro_density: (0 - 1) = 0.5
            a high density value increases the amount of orientation beats.
    """

    ratio2pitchclass_dict = globals_.RATIO2PITCHCLASS
    orchestration = globals_.ORCHESTRATION
    _segment_class = Verse
    _pickled_objects_path = "aml/transobjects"
    tools.igmkdir(_pickled_objects_path)
    _json_path = "{}/transobjects.json".format(_pickled_objects_path)

    def __init__(
        self,
        chapter: int = 59,
        verse: int = "opening",
        time_transcriber=transcriptions.TimeTranscriber(),
        octave_of_first_pitch: int = 0,
        use_full_scale: bool = False,
        tempo_factor: float = 0.5,
        harmonic_field_max_n_pitches: int = 4,
        harmonic_field_minimal_harmonicity: float = 0.135,
        harmonic_tolerance: float = 0.5,  # a very high harmonic tolerance won't add any
        # additional harmonic pitches, while a very low tolerance will try to add as many
        # additional harmonic pitches as possible.
        harmonic_pitches_add_artifical_harmonics: bool = True,
        harmonic_pitches_add_normal_pitches: bool = True,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch: tuple = (
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch: tuple = (
            1,
            0,
        ),
        max_rest_size_to_ignore: fractions.Fraction = fractions.Fraction(1, 4),
        maximum_deviation_from_center: float = 0.5,
        # rhythmical orientation data
        ro_temperature: float = 0.7,  # a low temperature increases the chance for a
        # beat to get added.
        ro_density: float = 0.5,  # a high density value increases the amount of
        # orientation beats.
        area_density_maker: infit.InfIt = infit.Gaussian(0.25, 0.075),  # a higher value
        # leads to more perforated melodic pitches.
        area_density_reference_size: fractions.Fraction = fractions.Fraction(1, 2),
    ) -> None:
        self.transcription = self._get_transcription(
            chapter=chapter,
            verse=verse,
            time_transcriber=time_transcriber,
            octave_of_first_pitch=octave_of_first_pitch,
            use_full_scale=use_full_scale,
        )
        self._transcription_melody = old.Melody(tuple(self.transcription[:]))
        self.areas = areas.Areas.from_melody(
            self._transcription_melody,
            self.transcription.spread_metrical_loop,
            area_density_maker,
            area_density_reference_size,
        )
        self.chapter = chapter
        self.verse = verse
        self.tempo_factor = tempo_factor
        self.bread = breads.Bread.from_melody(
            old.Melody(self.transcription).copy(),
            self.bars,
            max_rest_size_to_ignore,
            maximum_deviation_from_center,
        )

        self.assign_harmonic_pitches_to_slices(
            harmonic_tolerance,
            harmonic_pitches_add_artifical_harmonics,
            harmonic_pitches_add_normal_pitches,
            harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch,
            harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch,
        )
        self.assign_harmonic_fields_to_slices(
            harmonic_field_max_n_pitches, harmonic_field_minimal_harmonicity
        )

        self.rhythmic_orientation_indices = self._detect_rhythmic_orientation(
            temperature=ro_temperature, density=ro_density
        )

        self.melodic_orientation = self._make_melodic_orientation_system()
        self.rhythmic_orientation = self._make_rhythmic_orientation_system()

        super().__init__()

        self.attach(
            violin=strings.SilentStringMaker(globals_.VIOLIN),
            viola=strings.SilentStringMaker(globals_.VIOLA),
            cello=strings.SilentStringMaker(globals_.CELLO),
            keyboard=keyboard.SilentKeyboardMaker(),
        )

    @classmethod
    def _get_transcription(cls, **kwargs) -> transcriptions.Transcription:
        key = sorted(
            (
                (kw, kwargs[kw].json_key)
                if kw == "time_transcriber"
                else (kw, kwargs[kw])
                for kw in kwargs
            ),
            key=operator.itemgetter(0),
        )
        key = str(tuple(map(operator.itemgetter(1), key)))

        with open(cls._json_path, "r") as f:
            transobjects = json.loads(f.read())

        try:
            path = transobjects[key]

        except KeyError:
            transcription = transcriptions.QiroahTranscription.from_complex_scale(
                **kwargs
            )

            path = "{}/trans_{}_{}_{}".format(
                cls._pickled_objects_path,
                kwargs["chapter"],
                kwargs["verse"],
                uuid.uuid4().hex,
            )

            while path in os.listdir(cls._pickled_objects_path):
                path = "{}/trans_{}_{}_{}".format(
                    cls._pickled_objects_path,
                    kwargs["chapter"],
                    kwargs["verse"],
                    uuid.uuid4().hex,
                )

            transobjects.update({key: path})

            with open(path, "wb") as f:
                pickle.dump(transcription, f)

            with open(cls._json_path, "w") as f:
                f.write(json.dumps(transobjects))

        with open(path, "rb") as f:
            transcription = pickle.load(f)

        return transcription

    @staticmethod
    def _attach_double_barlines(staff, double_barlines_positions: tuple) -> None:
        for bar, has_double_bar_line in zip(staff, double_barlines_positions):
            if has_double_bar_line:
                try:
                    abjad.attach(abjad.BarLine(".", format_slot="before"), bar[0])
                # don't attach if there is already another bar line (perhaps from repeats)
                except abjad.PersistentIndicatorError:
                    pass

    def _find_double_barlines_positions(self) -> tuple:
        loop_size = self.transcription.spread_metrical_loop.loop_size
        loop_positions = tuple(
            True if idx % loop_size == 0 else False for idx in range(len(self.bars))
        )
        return mus.TrackMaker._adapt_bars_by_used_areas(loop_positions, self.used_areas)

    def __call__(self) -> Verse:
        verse = super().__call__()

        # add special bar lines at each start of a new loop
        double_barlines_positions = self._find_double_barlines_positions()
        for track_name in self.orchestration:
            if track_name in ("violin", "viola", "cello"):
                staves_to_attach_double_barlines = getattr(verse, track_name).abjad[1:2]
            else:
                staves_to_attach_double_barlines = getattr(verse, track_name).abjad

            for staff in staves_to_attach_double_barlines:
                if type(staff) == abjad.StaffGroup:
                    for sub_staff in staff:
                        self._attach_double_barlines(
                            sub_staff, double_barlines_positions
                        )
                else:
                    self._attach_double_barlines(staff, double_barlines_positions)

        # attach verse attribute (name or number of verse) to resulting verse object
        verse.verse = self.verse
        return verse

    def copy(self) -> "VerseMaker":
        return copy.deepcopy(self)

    @property
    def musdat(self) -> dict:
        return {
            "transcription": self._transcription_melody.copy(),
            "harmonic_pitches": self.harmonic_pitches,
        }

    @property
    def bars(self) -> tuple:
        return self.transcription.bars

    @property
    def tempo(self) -> int:
        return tools.find_closest_item(
            self.transcription.tempo * self.tempo_factor, globals_.STANDARD_TEMPI
        )

    @property
    def harmonic_pitches(self) -> tuple:
        last_pitch = self.bread[0].harmonic_pitch
        start = self.bread[0].start
        stop = self.bread[0].stop

        melody_pitch_starts = []

        if self.bread[0].does_slice_start_overlap_with_attack:
            melody_pitch_starts.append(self.bread[0].start)

        ns = []

        for slice_ in self.bread[1:]:
            if slice_.harmonic_pitch == last_pitch:
                stop = slice_.stop

                if slice_.does_slice_start_overlap_with_attack:
                    melody_pitch_starts.append(slice_.start)

            else:
                if last_pitch:
                    ns.append(
                        (
                            lily.NOvent(pitch=[last_pitch], delay=start, duration=stop),
                            tuple(melody_pitch_starts),
                        )
                    )

                start = slice_.start
                stop = slice_.stop
                last_pitch = slice_.harmonic_pitch
                melody_pitch_starts = []

                if slice_.does_slice_start_overlap_with_attack:
                    melody_pitch_starts.append(slice_.start)

        if last_pitch:
            ns.append(
                (
                    lily.NOvent(pitch=[last_pitch], delay=start, duration=stop),
                    tuple(melody_pitch_starts),
                )
            )

        return tuple(ns)

    @staticmethod
    def _filter_available_pitches_by_max_octave_difference(
        available_pitches: tuple,
        orientation_pitch: ji.JIPitch,
        maximum_octave_difference: tuple,
    ) -> tuple:
        orientation_octave = orientation_pitch.octave
        new_available_pitches = []
        for pitch in available_pitches:
            oct_difference = pitch.octave - orientation_octave
            appendable = False

            if oct_difference == 0:
                appendable = True
            elif oct_difference > 0:
                appendable = abs(oct_difference) <= maximum_octave_difference[1]
            else:
                appendable = abs(oct_difference) <= maximum_octave_difference[0]

            if appendable:
                new_available_pitches.append(pitch)

        if new_available_pitches:
            return tuple(new_available_pitches)

        else:
            return available_pitches

    @staticmethod
    def _register_harmonic_pitch(
        pitches2compare: tuple,
        harmonic_pitch: ji.JIPitch,
        get_available_pitches_from_adapted_instrument=None,
        maximum_octave_difference: tuple = None,
    ) -> ji.JIPitch:
        if get_available_pitches_from_adapted_instrument is None:

            def get_available_pitches_from_adapted_instrument(
                adapted_instrument,
            ) -> tuple:
                return adapted_instrument.available_pitches

        normalized_hp = harmonic_pitch.normalize()
        available_versions = tuple(
            p
            for p in get_available_pitches_from_adapted_instrument(
                globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[
                    globals_.PITCH2INSTRUMENT[normalized_hp]
                ]
            )
            if p.normalize() == normalized_hp
        )

        if maximum_octave_difference:
            sorted_pitches2compare = sorted(pitches2compare, key=lambda p: p.octave)
            available_versions = VerseMaker._filter_available_pitches_by_max_octave_difference(
                available_versions,
                sorted_pitches2compare[-1],
                maximum_octave_difference,
            )

        version_fitness_pairs = []
        for version in available_versions:
            harmonicity = 0
            for p2c in pitches2compare:
                if p2c:
                    harmonicity += (p2c - version).harmonicity_simplified_barlow
            version_fitness_pairs.append((version, harmonicity))

        return max(version_fitness_pairs, key=operator.itemgetter(1))[0]

    @staticmethod
    def _register_tonality_flux_pitch(
        melody_pitch0: ji.JIPitch,
        melody_pitch1: ji.JIPitch,
        tonality_flux_pitch0: ji.JIPitch,
        tonality_flux_pitch1: ji.JIPitch,
        get_available_pitches_from_adapted_instrument=None,
        maximum_octave_difference: int = 1,
    ) -> ji.JIPitch:
        if get_available_pitches_from_adapted_instrument is None:

            def get_available_pitches_from_adapted_instrument(
                adapted_instrument,
            ) -> tuple:
                return adapted_instrument.available_pitches

        octave_rating = {}
        available_octaves_per_pitch = []
        for tf_pitch, m_pitch in (
            (tonality_flux_pitch0, melody_pitch0),
            (tonality_flux_pitch1, melody_pitch1),
        ):
            normalized_hp = tf_pitch.normalize()
            available_versions = tuple(
                p
                for p in get_available_pitches_from_adapted_instrument(
                    globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[
                        globals_.PITCH2INSTRUMENT[normalized_hp]
                    ]
                )
                if p.normalize() == normalized_hp
            )
            if maximum_octave_difference is not None:
                available_versions = VerseMaker._filter_available_pitches_by_max_octave_difference(
                    available_versions, m_pitch, maximum_octave_difference
                )
            version_fitness_pairs = []
            for version in available_versions:
                harmonicity = (m_pitch - version).harmonicity_simplified_barlow
                version_fitness_pairs.append((version, harmonicity))

            sorted_version = tuple(
                map(
                    operator.itemgetter(0),
                    sorted(
                        version_fitness_pairs, key=operator.itemgetter(1), reverse=True
                    ),
                )
            )

            available_octaves = []
            for idx, pitch in enumerate(sorted_version):
                octave = pitch.octave
                if octave not in octave_rating:
                    octave_rating.update({octave: 0})

                octave_rating[octave] += idx
                available_octaves.append(octave)

            available_octaves_per_pitch.append(available_octaves)

        common_octaves = set(available_octaves_per_pitch[0]).intersection(
            available_octaves_per_pitch[1]
        )
        if common_octaves:
            best_octave = min(
                tuple((octave, octave_rating[octave]) for octave in common_octaves),
                key=operator.itemgetter(1),
            )[0]
            r0, r1 = (
                p.register(best_octave)
                for p in (tonality_flux_pitch0, tonality_flux_pitch1)
            )

        else:
            sorted_octaves = tuple(
                map(
                    operator.itemgetter(0),
                    (
                        sorted(
                            tuple(
                                (octave, octave_rating[octave])
                                for octave in octave_rating
                            ),
                            key=operator.itemgetter(1),
                        )
                    ),
                )
            )
            best_octaves = []
            for available_octaves in available_octaves_per_pitch:
                for octave in sorted_octaves:
                    if octave in available_octaves:
                        best_octaves.append(octave)
                        break
            r0, r1 = (
                p.register(octave)
                for p, octave in zip(
                    (tonality_flux_pitch0, tonality_flux_pitch1), best_octaves
                )
            )

        return r0, r1

    @staticmethod
    def _help_complex_melodic_intervals(
        tolerance: float,
        sd0: int,
        sd1: int,
        slice0: breads.Slice,
        slice1: breads.Slice,
        p0: ji.JIPitch,
        p1: ji.JIPitch,
        available_pitches_per_tone: tuple,
        maximum_octave_difference: tuple = (1, 1),
    ) -> None:
        closeness0, closeness1 = (
            globals_.CLOSENESS_FROM_PX_TO_PY[p0][p1],
            globals_.CLOSENESS_FROM_PX_TO_PY[p1][p0],
        )

        # complex melodic interval
        if any((closeness0 < tolerance, closeness1 < tolerance)):
            available_pitches = set(available_pitches_per_tone[0]).intersection(
                set(available_pitches_per_tone[1])
            )
            available_pitches = tuple(
                p
                for p in available_pitches
                # forbid pitches that are either in already used scale_degrees or that are
                # part of auxiliary scale-degrees 4 and 7.
                if globals_.PITCH2SCALE_DEGREE[p] not in (sd0, sd1, 3, 6)
            )
            ap_closeness_to_p0, ap_closeness_to_p1 = (
                tuple(
                    globals_.CLOSENESS_FROM_PX_TO_PY[p][app]
                    for app in available_pitches
                )
                for p in (p0, p1)
            )

            # find factors for each melodic pitch according to their duration (it is more
            # important to have a harmonic interval between the longer lasting pitch)
            slices_duration = tuple(s.stop - s.start for s in (slice0, slice1))
            summed_duration = sum(slices_duration)
            duration_factor0, duration_factor1 = (
                dur / summed_duration for dur in slices_duration
            )

            available_pitches_and_fitness = tuple(
                (p, (c0 * duration_factor0) + (c1 * duration_factor1))
                for p, c0, c1 in zip(
                    available_pitches, ap_closeness_to_p0, ap_closeness_to_p1
                )
                if c0 > closeness0 and c1 > closeness1
            )
            if available_pitches_and_fitness:
                harmonic_pitch = max(
                    available_pitches_and_fitness, key=operator.itemgetter(1)
                )[0]

                registered_harmonic_pitch = VerseMaker._register_harmonic_pitch(
                    (slice0.melody_pitch, slice1.melody_pitch),
                    harmonic_pitch,
                    maximum_octave_difference=maximum_octave_difference,
                )
                slice0.harmonic_pitch = registered_harmonic_pitch
                slice1.harmonic_pitch = registered_harmonic_pitch

    @staticmethod
    def _help_tonality_flux(
        scale_degree: int,
        slice0: breads.Slice,
        slice1: breads.Slice,
        p0: ji.JIPitch,
        p1: ji.JIPitch,
        available_pitches_per_tone: tuple,
        # harmonicity_border for intervals in parallel movement
        harmonicity_border: float = ji.r(7, 6).harmonicity_simplified_barlow,
        # minimal harmonic closeness for intervals in counter movement
        min_closeness: float = 0.75,
        maximum_octave_difference: tuple = (1, 1),
        get_available_pitches_from_adapted_instrument=None,
    ) -> None:
        movement_direction = slice0.melody_pitch < slice1.melody_pitch

        # (1) find pitches for microtonal parallel or counter movement of voices
        parallel_candidates = []
        counter_candidates = []
        for sd in range(7):
            if sd != scale_degree:
                avp0, avp1 = tuple(
                    tuple(p for p in avp if globals_.PITCH2SCALE_DEGREE[p] == sd)
                    for avp in available_pitches_per_tone
                )
                intervals0, intervals1 = tuple(
                    tuple((main_pitch - side_pitch).normalize() for side_pitch in avp)
                    for main_pitch, avp in ((p0, avp0), (p1, avp1))
                )

                for it0, it1 in itertools.product(intervals0, intervals1):

                    relevant_pitch0 = avp0[intervals0.index(it0)]
                    relevant_pitch1 = avp1[intervals1.index(it1)]
                    rp_movement_direction = relevant_pitch0 < relevant_pitch1

                    if it0 == it1 or it0 == it1.inverse().normalize():
                        harmonicity = it0.harmonicity_simplified_barlow
                        if harmonicity >= harmonicity_border:
                            parallel_candidates.append(
                                ((relevant_pitch0, relevant_pitch1), harmonicity)
                            )

                    if movement_direction != rp_movement_direction:
                        closeness0 = globals_.CLOSENESS_FROM_PX_TO_PY[p0][
                            relevant_pitch0
                        ]
                        closeness1 = globals_.CLOSENESS_FROM_PX_TO_PY[p1][
                            relevant_pitch1
                        ]
                        tests = (closeness0 > min_closeness, closeness1 > min_closeness)
                        if all(tests):
                            counter_candidates.append(
                                (
                                    (relevant_pitch0, relevant_pitch1),
                                    closeness0 + closeness1,
                                )
                            )

        if parallel_candidates:
            hp0, hp1 = max(parallel_candidates, key=operator.itemgetter(1))[0]

        elif counter_candidates:
            hp0, hp1 = max(counter_candidates, key=operator.itemgetter(1))[0]

        else:
            hp0, hp1 = (
                max(
                    (
                        (hp, globals_.CLOSENESS_FROM_PX_TO_PY[mp][hp])
                        for hp in avp
                        if globals_.PITCH2SCALE_DEGREE[hp] != scale_degree
                    ),
                    key=operator.itemgetter(1),
                )[0]
                for mp, avp in zip((p0, p1), available_pitches_per_tone)
            )

        registered_hp0, registered_hp1 = VerseMaker._register_tonality_flux_pitch(
            slice0.melody_pitch,
            slice1.melody_pitch,
            hp0,
            hp1,
            get_available_pitches_from_adapted_instrument,
            maximum_octave_difference,
        )

        slice0.harmonic_pitch = registered_hp0
        slice1.harmonic_pitch = registered_hp1

    def assign_harmonic_pitches_to_slices(
        self,
        tolerance: float = 0.5,
        add_artifical_harmonics: bool = True,
        add_normal_pitches: bool = True,
        tonality_flux_maximum_octave_difference: tuple = (1, 1),
        harmonic_pitch_maximum_octave_difference: tuple = (1, 1),
    ) -> None:

        if add_artifical_harmonics and add_normal_pitches:
            get_available_pitches_from_adapted_instrument = None
        elif add_artifical_harmonics:

            def get_available_pitches_from_adapted_instrument(ai):
                return ai.harmonic_pitches

        else:

            def get_available_pitches_from_adapted_instrument(ai):
                return ai.normal_pitches

        for slice0, slice1 in zip(self.bread, self.bread[1:]):
            tests = (
                slice0.melody_pitch != slice1.melody_pitch,
                slice0.melody_pitch,
                slice1.melody_pitch,
            )
            if all(tests):
                p0, p1 = (
                    slice0.melody_pitch.normalize(),
                    slice1.melody_pitch.normalize(),
                )

                sd0, sd1 = (
                    globals_.PITCH2SCALE_DEGREE[p0],
                    globals_.PITCH2SCALE_DEGREE[p1],
                )

                available_pitches_per_tone = tuple(
                    tuple(
                        sp.normalize()
                        for sp in functools.reduce(
                            operator.add,
                            tuple(
                                globals_.SCALE_PER_INSTRUMENT[instr]
                                for instr in ("cello", "violin", "viola")
                                if instr != globals_.PITCH2INSTRUMENT[p]
                            ),
                        )
                    )
                    for p in (p0, p1)
                )

                # tonality flux
                if sd0 == sd1:
                    self._help_tonality_flux(
                        sd0,
                        slice0,
                        slice1,
                        p0,
                        p1,
                        available_pitches_per_tone,
                        maximum_octave_difference=tonality_flux_maximum_octave_difference,
                        get_available_pitches_from_adapted_instrument=get_available_pitches_from_adapted_instrument,
                    )

                    slice0.has_tonality_flux = True
                    slice1.has_tonality_flux = True

                # complex melodic interval
                else:
                    self._help_complex_melodic_intervals(
                        tolerance,
                        sd0,
                        sd1,
                        slice0,
                        slice1,
                        p0,
                        p1,
                        available_pitches_per_tone,
                        maximum_octave_difference=harmonic_pitch_maximum_octave_difference,
                    )

        self.bread.extend_harmonic_pitches()

    @staticmethod
    def _get_harmonicity_of_harmony(harmony: tuple) -> float:
        return sum(
            globals_.HARMONICITY_NET[tuple(sorted(c))]
            for c in itertools.combinations(harmony, 2)
        )

    def _find_harmonic_field_candidates(
        self,
        idx: int,
        slice_: breads.Slice,
        max_n_pitches: int,
        minimal_harmonicity_for_pitch: float,
    ) -> tuple:
        hf = tuple(
            p.normalize() for p in (slice_.melody_pitch, slice_.harmonic_pitch) if p
        )

        if hf:
            available_pitches_per_scale_degree = [
                tuple(into.normalize() for into in intonations)
                for intonations in globals_.INTONATIONS_PER_SCALE_DEGREE
            ]
            prohibited_scale_degrees_for_added_pitches = set(
                globals_.PITCH2SCALE_DEGREE[p] for p in hf
            )

            try:
                previous_slice = self.bread[idx - 1]
            except IndexError:
                previous_slice = None

            try:
                next_slice = self.bread[idx + 1]
            except IndexError:
                next_slice = None

            if next_slice and next_slice.melody_pitch:
                prohibited_scale_degrees_for_added_pitches.add(
                    globals_.PITCH2SCALE_DEGREE[next_slice.melody_pitch.normalize()]
                )

            for neighbour in (s for s in (previous_slice, next_slice) if s):
                if neighbour:
                    neighbour_pitches = (
                        np.normalize()
                        for np in (neighbour.melody_pitch, neighbour.harmonic_pitch)
                        if np
                    )
                    for np in neighbour_pitches:
                        available_pitches_per_scale_degree[
                            globals_.PITCH2SCALE_DEGREE[np]
                        ] = tuple(
                            p
                            for p in available_pitches_per_scale_degree[
                                globals_.PITCH2SCALE_DEGREE[np]
                            ]
                            if p == np
                        )

            allowed_scale_degrees = tuple(
                sd
                for sd, available_intonations in enumerate(
                    available_pitches_per_scale_degree
                )
                if sd not in prohibited_scale_degrees_for_added_pitches
                and available_intonations
            )

            n_missing_pitches = max_n_pitches - len(hf)

            n_items = min((n_missing_pitches, len(allowed_scale_degrees)))

            if n_items > 0:
                candidates = []

                for combination in itertools.combinations(
                    allowed_scale_degrees, n_items
                ):
                    combination = tuple(
                        available_pitches_per_scale_degree[idx] for idx in combination
                    )
                    for added_pitches in itertools.product(*combination):
                        nhf = hf + tuple(added_pitches)

                        # discard added pitches if their harmonicity value is too low

                        if minimal_harmonicity_for_pitch:
                            div = len(nhf) - 1
                            pitch2fitnenss = {
                                p: sum(
                                    globals_.HARMONICITY_NET[tuple(sorted((p, p1)))]
                                    for p1 in nhf
                                    if p != p1
                                )
                                / div
                                for p in nhf
                            }

                            nhf = tuple(
                                p
                                for p in nhf
                                if p in hf
                                or pitch2fitnenss[p] > minimal_harmonicity_for_pitch
                            )

                        harmonicity = self._get_harmonicity_of_harmony(nhf)

                        # only check for added pitches
                        scale_degree2pitch = {
                            globals_.PITCH2SCALE_DEGREE[p]: p
                            for p in tuple(added_pitches)
                        }

                        candidates.append((nhf, harmonicity, scale_degree2pitch))

                return tuple(
                    sorted(candidates, key=operator.itemgetter(1), reverse=True)
                )

            return ((hf, self._get_harmonicity_of_harmony(hf), {}),)

    @staticmethod
    def _find_harmonic_fields(candidates_per_slice: tuple) -> tuple:
        def test_for_tonality_flux(choosen_candidates: tuple) -> bool:
            for candidate0, candidate1 in zip(
                choosen_candidates, choosen_candidates[1:]
            ):
                scale_degree2pitch0, scale_degree2pitch1 = candidate0[2], candidate1[2]
                for sd in scale_degree2pitch0:
                    if sd in scale_degree2pitch1:
                        if scale_degree2pitch0[sd] != scale_degree2pitch1[sd]:
                            return False

            return True

        return tools.complex_backtracking(
            candidates_per_slice, (test_for_tonality_flux,)
        )

    def assign_harmonic_fields_to_slices(
        self, max_n_pitches: int = 4, minimal_harmonicity_for_pitch: float = None
    ) -> None:
        candidates_per_slice = []
        for idx, slice_ in enumerate(self.bread):
            candidates_per_slice.append(
                self._find_harmonic_field_candidates(
                    idx, slice_, max_n_pitches, minimal_harmonicity_for_pitch
                )
            )

        candidates2analyse = tools.split_iterable_by_n(candidates_per_slice, None)
        harmonic_field_per_slice = []
        for candidates in candidates2analyse:
            can = candidates[:-1]
            if can:
                for solution in self._find_harmonic_fields(can):
                    pitches = solution[0]
                    div_fitness = len(pitches) - 1

                    if div_fitness == 0:
                        div_fitness = 1

                    pitch2fitnenss = {
                        p: sum(
                            globals_.HARMONICITY_NET[tuple(sorted((p, p1)))]
                            for p1 in pitches
                            if p != p1
                        )
                        / div_fitness
                        for p in pitches
                    }
                    harmonic_field_per_slice.append(pitch2fitnenss)
            if candidates[-1] is None:
                harmonic_field_per_slice.append(None)

        for slice_, field in zip(self.bread, harmonic_field_per_slice):
            if field:
                slice_.harmonic_field = field

    def _make_melodic_orientation_system(self) -> lily.NOventLine:
        orientation = lily.NOventLine([])

        for tone in self.musdat["transcription"]:
            if tone.pitch.is_empty:
                pitch = []
                markup = None
            else:
                instrument = globals_.INSTRUMENT_NAME2OBJECT[
                    globals_.PITCH2INSTRUMENT[tone.pitch.normalize()]
                ]
                pitch = [tone.pitch]
                markup = attachments.MarkupOnOff(
                    "\\small {}".format(instrument.short_name), direction="up"
                )

            novent = lily.NOvent(
                pitch=pitch,
                delay=tone.delay,
                duration=tone.duration,
                markup_on_off=markup,
            )
            orientation.append(novent)

        duration = orientation.duration
        difference = self.duration - duration
        if difference > 0:
            orientation.append(
                lily.NOvent(pitch=[], delay=difference, duration=difference)
            )

        return orientation

    def _make_rhythmic_orientation_system(self) -> lily.NOventLine:
        absolute_positions = self.transcription.spread_metrical_loop.get_all_rhythms()
        absolute_rhythm = tuple(
            absolute_positions[index] for index in self.rhythmic_orientation_indices
        )
        is_first_attack_rest = False
        if absolute_rhythm[0] != 0:
            absolute_rhythm = (0,) + absolute_rhythm
            is_first_attack_rest = True

        relative_rhythm = tuple(
            b - a
            for a, b in zip(
                absolute_rhythm,
                absolute_rhythm[1:]
                + (self.transcription.spread_metrical_loop.duration,),
            )
        )

        is_first = True
        orientation = lily.NOventLine([])
        for rhythm in relative_rhythm:
            if is_first and is_first_attack_rest:
                pitch = []
                is_first = False

            else:
                pitch = [ji.r(1, 1)]

            novent = lily.NOvent(pitch=pitch, delay=rhythm, duration=rhythm)
            orientation.append(novent)

        return orientation

    def _detect_rhythmic_orientation(
        self, density: float = 0.5, temperature: float = 0.65
    ) -> tuple:
        """Return indices of beats that are part of rhythmic orientation."""

        for percent in (density, temperature):
            assert percent >= 0 and percent <= 1

        spread_metrical_loop = self.transcription.spread_metrical_loop

        pairs = spread_metrical_loop.get_all_rhythm_metricitiy_pairs()
        n_beats = len(pairs)
        average_distance_between_two_attacks = n_beats / (n_beats * density)

        indices = []
        for idx, pair in enumerate(pairs):
            rhythm, metricity = pair
            primes = spread_metrical_loop.get_primes_of_absolute_rhythm(rhythm)
            # get responsible slice for the current rhythmical position
            slice_ = self.bread.find_responsible_slices(rhythm, rhythm + 1)[0]

            # check if point is inhabited by any allowed pitch(es)
            is_inhabited = False
            if slice_.harmonic_field:
                available_instruments = tuple(
                    spread_metrical_loop.prime_instrument_mapping[prime]
                    for prime in primes
                )
                available_pitches = tuple(
                    p
                    for p in slice_.harmonic_field
                    # only use pitches that are available in the instrument that are
                    # allowed to play during this beat
                    if globals_.PITCH2INSTRUMENT[p] in available_instruments
                    # prohibit auxiliary pitches for rhythmic orientation
                    and globals_.PITCH2SCALE_DEGREE[p] not in (3, 6)
                )

                if available_pitches:
                    is_inhabited = True

            if is_inhabited:
                ratio = (4, 3, 2)

                if indices:
                    distance_to_last_index = idx - indices[-1]

                    if distance_to_last_index >= average_distance_between_two_attacks:
                        energy_by_density_and_equilibrium = 1

                    else:
                        energy_by_density_and_equilibrium = tools.scale(
                            (
                                1,
                                distance_to_last_index,
                                average_distance_between_two_attacks,
                            ),
                            0,
                            1,
                        )[1]

                else:
                    energy_by_density_and_equilibrium = 1

                energy_items = (
                    metricity,
                    energy_by_density_and_equilibrium,
                    len(available_instruments) / 3,
                )
                energy_level = sum(
                    item * factor for item, factor in zip(energy_items, ratio)
                )
                energy_level /= sum(ratio)
                if energy_level > temperature:
                    indices.append(idx)

        return tuple(indices)
