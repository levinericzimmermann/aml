import quicktions as fractions

import abjad

from mu.utils import tools

from mutools import mus
from mutools import synthesis

from aml import globals_


class AMLTrack(mus.Track):
    format = globals_.FORMAT

    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        title: str = None,
        resolution: int = None,
    ):
        self.title = title
        super().__init__(abjad_data, sound_engine, resolution=resolution)

    def _make_score_block(self, make_layout_block: bool = False) -> abjad.LilyPondFile:
        score_block = super()._make_score_block(make_layout_block)
        local_header = abjad.Block("header")
        local_header.piece = abjad.Markup(
            abjad.MarkupCommand(
                "center-column",
                [
                    abjad.MarkupCommand("vspace", 0),
                    abjad.MarkupCommand(
                        "rounded-box",
                        [
                            abjad.MarkupCommand("fontsize", 1.5),
                            abjad.MarkupCommand("smallCaps"),
                            "{}".format(self.title),
                        ],
                    ),
                ],
            )
        )
        score_block.items.append(local_header)
        return score_block


class AMLTrackMaker(mus.TrackMaker):
    def attach(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> None:
        super().attach(segment_maker, meta_track)
        self._title = "{}.{}".format(segment_maker.chapter, segment_maker.verse)

    @property
    @mus._not_attached_yet
    def title(self) -> str:
        return self._title

    @property
    def absolute_bar_durations(self) -> tuple:
        return tools.accumulate_from_zero(
            tuple(fractions.Fraction(ts.duration) for ts in self.bars)
        )

    def get_responsible_bar_index(self, start: fractions.Fraction) -> int:
        abd = self.absolute_bar_durations
        for bidx, bstart, bstop in zip(range(len(self.bars)), abd, abd[1:]):
            if start >= bstart and start < bstop:
                return bidx

        raise ValueError()
