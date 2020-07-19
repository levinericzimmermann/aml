import abjad

from mutools import mus
from mutools import synthesis


class AMLTrack(mus.Track):
    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        title: str = None,
        resolution: int = None,
    ):
        self.title = title
        super().__init__(abjad_data, sound_engine, resolution=resolution)

    def _make_lilypond_file(self) -> abjad.LilyPondFile:
        lpf = super()._make_lilypond_file()
        lpf.header_block.piece = abjad.Markup(
            abjad.MarkupCommand(
                "center-column",
                [
                    abjad.MarkupCommand("fontsize", -1.95),
                    abjad.MarkupCommand("smallCaps"),
                    "{}".format(self.title),
                    abjad.MarkupCommand("vspace", -0.8),
                ],
            )
        )
        return lpf


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
