import functools
import itertools
import operator

import abjad
import quicktions as fractions

from mu.mel import ji
from mu.sco import old
from mu.utils import tools

from mutools import attachments
from mutools import lily
from mutools import mus

from aml import breads
from aml import globals_
from aml import transcriptions
from aml.trackmaker import keyboard
from aml.trackmaker import strings


class Verse(mus.Segment):
    @property
    def score(self) -> abjad.Score:
        # removing orientation lines in all-instruments-score
        sco = abjad.Score([])
        for track_name in self.orchestration:
            abjad_data = abjad.mutate(getattr(self, track_name).abjad).copy()[-1]
            """
            if track_name in ("cello", "violin", "viola"):
                abjad_data = abjad_data[-1]
            else:
                abjad_data = abjad_data[-2:]
            """
            sco.append(abjad_data)
        return sco


class VerseMaker(mus.SegmentMaker):
    ratio2pitchclass_dict = globals_.RATIO2PITCHCLASS
    orchestration = globals_.ORCHESTRATION
    _segment_class = Verse

    def __init__(
        self,
        chapter: int = 59,
        verse: int = "opening",
        time_transcriber=transcriptions.TimeTranscriber(),
        octave_of_first_pitch: int = 0,
        use_full_scale: bool = False,
        tempo_factor: float = 0.5,
        harmonic_tolerance: float = 0.5,
        max_rest_size_to_ignore: fractions.Fraction = fractions.Fraction(1, 4),
        maximum_deviation_from_center: float = 0.5,
    ) -> None:
        self.transcription = transcriptions.QiroahTranscription.from_complex_scale(
            chapter=chapter,
            verse=verse,
            time_transcriber=time_transcriber,
            octave_of_first_pitch=octave_of_first_pitch,
            use_full_scale=use_full_scale,
        )
        self._transcription_melody = old.Melody(tuple(self.transcription[:]))
        self.chapter = chapter
        self.verse = verse
        self.tempo_factor = tempo_factor
        self.bread = breads.Bread.from_melody(
            old.Melody(self.transcription).copy(),
            self.bars,
            max_rest_size_to_ignore,
            maximum_deviation_from_center,
        )

        self.assign_harmonic_pitches_to_slices(harmonic_tolerance)
        self.assign_harmonic_fields_to_slices()
        self.melodic_orientation = self._make_melodic_orientation_system()

        super().__init__()

        self.attach(
            violin=strings.SilentStringMaker(abjad.Violin()),
            viola=strings.SilentStringMaker(abjad.Viola()),
            cello=strings.SilentStringMaker(abjad.Cello()),
            keyboard=keyboard.SilentKeyboardMaker(),
        )

    def __call__(self) -> Verse:
        verse = super().__call__()
        # attach verse attribute (name or number of verse) to resulting verse object
        verse.verse = self.verse
        return verse

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
    def harmonic_pitches(self) -> lily.NOventSet:
        last_pitch = self.bread[0].harmonic_pitch
        start = self.bread[0].start
        stop = self.bread[0].stop

        ns = lily.NOventSet(size=self.bread[-1].stop)
        for slice_ in self.bread[1:]:
            if slice_.harmonic_pitch == last_pitch:
                stop = slice_.stop

            else:
                if last_pitch:
                    ns.append(
                        lily.NOvent(pitch=[last_pitch], delay=start, duration=stop)
                    )

                start = slice_.start
                stop = slice_.stop
                last_pitch = slice_.harmonic_pitch

        if last_pitch:
            ns.append(lily.NOvent(pitch=[last_pitch], delay=start, duration=stop))

        return ns

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
                if globals_.PITCH2SCALE_DEGREE[p] not in (sd0, sd1)
            )
            ap_closeness_to_p0, ap_closeness_to_p1 = (
                tuple(
                    globals_.CLOSENESS_FROM_PX_TO_PY[p][app]
                    for app in available_pitches
                )
                for p in (p0, p1)
            )
            available_pitches_and_fitness = tuple(
                (p, c0 + c1)
                for p, c0, c1 in zip(
                    available_pitches, ap_closeness_to_p0, ap_closeness_to_p1
                )
                if c0 > closeness0 and c1 > closeness1
            )
            if available_pitches_and_fitness:
                harmonic_pitch = max(
                    available_pitches_and_fitness, key=operator.itemgetter(1)
                )[0]
                slice0.harmonic_pitch = harmonic_pitch
                slice1.harmonic_pitch = harmonic_pitch

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

        slice0.harmonic_pitch = hp0
        slice1.harmonic_pitch = hp1

    def assign_harmonic_pitches_to_slices(self, tolerance: float = 0.5) -> None:
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
                        sd0, slice0, slice1, p0, p1, available_pitches_per_tone
                    )

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
                    )

        self.bread.extend_harmonic_pitches()

    @staticmethod
    def _get_harmonicity_of_harmony(harmony: tuple) -> float:
        return sum(
            globals_.HARMONICITY_NET[tuple(sorted(c))]
            for c in itertools.combinations(harmony, 2)
        )

    def _find_harmonic_field_candidates(
        self, idx: int, slice_: breads.Slice, max_n_pitches: int
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
                        # only check for added pitches
                        scale_degree2pitch = {
                            globals_.PITCH2SCALE_DEGREE[p]: p
                            for p in tuple(added_pitches)
                        }
                        harmonicity = self._get_harmonicity_of_harmony(nhf)
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

    def assign_harmonic_fields_to_slices(self, max_n_pitches: int = 4) -> None:
        candidates_per_slice = []
        for idx, slice_ in enumerate(self.bread):
            candidates_per_slice.append(
                self._find_harmonic_field_candidates(idx, slice_, max_n_pitches)
            )

        candidates2analyse = tools.split_iterable_by_n(candidates_per_slice, None)
        harmonic_field_per_slice = []
        for candidates in candidates2analyse:
            can = candidates[:-1]
            if can:
                for solution in self._find_harmonic_fields(can):
                    pitches = solution[0]
                    pitch2fitnenss = {
                        p: sum(
                            globals_.HARMONICITY_NET[tuple(sorted((p, p1)))]
                            for p1 in pitches
                            if p != p1
                        )
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
                markup = attachments.Markup("\\small {}".format(instrument.short_name))

            novent = lily.NOvent(
                pitch=pitch, delay=tone.delay, duration=tone.duration, markup=markup
            )
            orientation.append(novent)

        duration = orientation.duration
        difference = self.duration - duration
        if difference > 0:
            orientation.append(
                lily.NOvent(pitch=[], delay=difference, duration=difference)
            )

        return orientation
