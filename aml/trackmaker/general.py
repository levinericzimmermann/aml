import abjad

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

    def _make_score_block(self) -> abjad.LilyPondFile:
        score_block = super()._make_score_block()
        local_header = abjad.Block("header")
        local_header.piece = abjad.Markup(
            abjad.MarkupCommand(
                "center-column",
                [
                    abjad.MarkupCommand("fontsize", 1.5),
                    abjad.MarkupCommand("smallCaps"),
                    "{}".format(self.title),
                    abjad.MarkupCommand("vspace", 0),
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
