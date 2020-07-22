import importlib
import os

import PIL

import abjad

from mu.utils import tools

from mutools import mus

from aml import globals_
from aml import versemaker


class Chapter(object):
    _build_path = "aml/build/chapters"

    sco_name = "notation"
    sf_name = "synthesis"

    make_png = False

    def __init__(self, name: str, *verse: versemaker.Verse, title: str = None):
        self._chapter_path = "{}/{}".format(self._build_path, name)
        self._notation_path = "{}/{}/notation".format(self._build_path, name)
        self._name = name
        self._title = title
        self._verses = self._sort_verses(verse)

        tools.igmkdir(self.path)
        tools.igmkdir(self.notation_path)

    @classmethod
    def from_path(
        cls,
        path: str = "aml/composition/al-hasyr",
        allowed_verses: tuple = None,
        title: str = None,
    ) -> "Chapter":
        name = path.split("/")[-1]

        verses = []
        for fl in os.listdir(path):
            if fl[-2:] == "py":
                is_appendable = True
                verse_name = fl[:-3]
                if allowed_verses and verse_name not in allowed_verses:
                    is_appendable = False

                if is_appendable:
                    local_path = "{}/{}".format(path, fl[:-3])
                    module = local_path.replace("/", ".")
                    split_position = module.index(".")
                    module, relative_path = (
                        module[:split_position],
                        module[split_position:],
                    )
                    verses.append(importlib.import_module(relative_path, module).main())

        return cls(name, *verses, title=title)

    @staticmethod
    def _sort_verses(verses: tuple) -> tuple:
        opening_and_closing_verses = []
        in_between_verses = []
        for verse in verses:
            if verse.verse in ("opening", "closing"):
                opening_and_closing_verses.append(verse)
            else:
                in_between_verses.append(verse)

        sorted_in_between_verses = sorted(
            in_between_verses, key=lambda verse: int(verse.verse)
        )

        for verse in opening_and_closing_verses:
            if verse.verse == "opening":
                sorted_in_between_verses = [verse] + sorted_in_between_verses
            elif verse.verse == "closing":
                sorted_in_between_verses += [verse]

        return tuple(sorted_in_between_verses)

    @property
    def name(self) -> str:
        return self._name

    @property
    def verses(self) -> tuple:
        return self._verses

    @property
    def path(self) -> str:
        return self._chapter_path

    @property
    def notation_path(self) -> str:
        return self._notation_path

    def _render_verses(self, render_each_track: bool = True) -> None:
        """Generate notation & sound files for each instrument in each verse."""

        notation_processes = []
        for verse in self.verses:

            verse_path = "{}/{}".format(self.path, verse.verse)
            tools.igmkdir(verse_path)

            verse.synthesize(verse_path, self.sf_name, render_each_track)
            verse.notate("{}/{}".format(verse_path, self.sco_name))

            for meta_track in globals_.ORCHESTRATION:
                instrument_path = "{}/{}".format(verse_path, meta_track)
                tools.igmkdir(instrument_path)

                track = getattr(verse, meta_track)
                if self.make_png:
                    notation_processes.append(
                        track.notate("{}/{}".format(instrument_path, self.sco_name))
                    )

        for process in notation_processes:
            process.wait()

    def _make_png_notation_for_each_instrument(self) -> None:
        A2_inches = (23.4, 16.5)
        A2_pixel = tuple(int(inch * mus.STANDARD_RESOLUTION) for inch in A2_inches)

        distance_width = 0.25  # inches
        distance_width = int(distance_width * mus.STANDARD_RESOLUTION)

        for meta_track in globals_.ORCHESTRATION:
            notation_path = "{}/notation/{}.pdf".format(self.path, meta_track)
            image = PIL.Image.new("RGB", A2_pixel, "white")
            images2paste = []
            for verse in self.verses:
                verse_path = "{}/{}".format(self.path, verse.verse)
                instrument_path = "{}/{}".format(verse_path, meta_track)
                sco_path = "{}/{}.png".format(instrument_path, self.sco_name)
                sco_image = PIL.Image.open(sco_path)
                images2paste.append(sco_image)

            height_per_image = tuple(img.height for img in images2paste)
            summed_height_per_image = sum(height_per_image)
            remaining_space = image.height - summed_height_per_image
            assert remaining_space >= 0

            n_areas_inbetween = len(images2paste) + 1
            n_pixels_in_between = int(remaining_space / n_areas_inbetween)

            current_height = n_pixels_in_between
            for img in images2paste:
                image.paste(img, (distance_width, current_height))
                current_height += img.height + n_pixels_in_between

            image.save(notation_path, resolution=mus.STANDARD_RESOLUTION)

    def _make_pdf_notation_for_each_instrument(self) -> None:
        for meta_track in globals_.ORCHESTRATION:
            notation_path = "{}/notation/{}".format(self.path, meta_track)
            is_first = True
            for verse in self.verses:
                track = getattr(verse, meta_track)
                if is_first:
                    lpf = track._make_lilypond_file()
                    is_first = False
                else:
                    lpf.items.append(track._make_score_block())

            if self._title:
                lpf.header_block.title = abjad.Markup(self._title)

            track._notate(notation_path, lpf)

    def _make_notation_for_each_instrument(self) -> None:
        if self.make_png:
            self._make_png_notation_for_each_instrument()
        else:
            self._make_pdf_notation_for_each_instrument()

    def __call__(
        self, render_verses: bool = True, render_each_instrument: bool = True
    ) -> None:
        """Generate png file for each instrument."""

        if render_verses:
            self._render_verses(render_each_instrument)

        self._make_notation_for_each_instrument()
