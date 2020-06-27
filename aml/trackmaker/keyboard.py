import functools
import operator
import subprocess

import abjad
import quicktions as fractions

from mu.sco import old
from mu.utils import infit
from mu.utils import tools

from mutools import attachments
from mutools import mus
from mutools import lily
from mutools import synthesis

from aml import comprovisation
from aml import globals_


class Keyboard(mus.Track):
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

        for staff in abjad_data[1:]:
            abjad.attach(
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
        abjad.attach(abjad.Clef("bass"), abjad_data[1][1][0][0])

        super().__init__(abjad_data, sound_engine, resolution)


class LeftHandKeyboardEngine(synthesis.PyteqEngine):
    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )
        super().__init__(
            # fxp="aml/keyboard_setups/fxp/VibraphoneV-BHumanizednostretching.fxp"
            preset='"Erard Player"'
        )

    @property
    def CONCERT_PITCH(self) -> float:
        return globals_.CONCERT_PITCH

    def render(self, name: str) -> subprocess.Popen:
        return super().render(name, self._novent_line)


class SilentKeyboardMaker(mus.TrackMaker):
    _track_class = Keyboard

    @staticmethod
    def _prepare_staves(
        polyline: old.PolyLine, segment_maker: mus.SegmentMaker
    ) -> old.PolyLine:
        polyline[1][0].margin_markup = attachments.MarginMarkup(
            "{}.{}".format(segment_maker.chapter, segment_maker.verse),
            context="StaffGroup",
        )

        for nol in polyline:
            nol[0].tempo = attachments.Tempo((1, 4), segment_maker.tempo)

        return old.PolyLine(polyline)

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        return self._prepare_staves(pl, segment_maker)

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return synthesis.SilenceEngine(1)


class KeyboardMaker(SilentKeyboardMaker):
    def __init__(
        self,
        n_beats_per_bar: infit.InfIt = infit.Cycle((4, 3, 5, 4)),
        grid_size: fractions.Fraction = fractions.Fraction(1, 8),
    ):
        self.n_beats_per_bar = n_beats_per_bar
        self.grid_size = grid_size

    def _make_simple_left_hand(
        self, segment_maker: mus.SegmentMaker
    ) -> lily.NOventLine:
        grid = tools.accumulate_from_zero(
            tuple(
                self.grid_size for n in range(segment_maker.duration // self.grid_size)
            )
        )
        stressed_beats = tools.accumulate_from_zero(
            functools.reduce(
                operator.add,
                tuple(
                    tuple(
                        n * self.grid_size
                        for n in tools.euclid(
                            float(ts.duration) // self.grid_size,
                            next(self.n_beats_per_bar),
                        )
                    )
                    for ts in segment_maker.bars
                ),
            )
        )
        nl = lily.NOventLine([])
        for start, stop in zip(grid, grid[1:]):
            delay = stop - start
            slices = segment_maker.bread.find_responsible_slices(start, stop)

            is_addable = True
            try:
                assert len(slices) == 1
            except AssertionError:
                print("warning {} slices for {} / {}".format(len(slices), start, stop))
                if len(slices) == 0:
                    is_addable = False

            if is_addable and slices[0].harmonic_field:
                slice_ = slices[0]
                pitches = [p.register(-1) for p in slice_.harmonic_field]
                no = lily.NOvent(pitches, delay=delay, duration=delay)

                if start in stressed_beats:
                    no.choose = attachments.Choose()
                    no.dynamic = attachments.Dynamic("mp")
                    no.optional = None
                    no.volume = 0.7

                else:
                    no.optional = attachments.Optional()
                    no.choose = attachments.ChooseOne()
                    no.dynamic = attachments.Dynamic("p")
                    no.volume = 0.55
            else:
                no = lily.NOvent([], delay=delay, duration=delay)

            nl.append(no)

        nl = nl.tie_pauses()

        return nl

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        pl[-1] = self._make_simple_left_hand(segment_maker)

        return self._prepare_staves(pl, segment_maker)

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return LeftHandKeyboardEngine(
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[2])
        )
