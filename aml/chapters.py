import importlib
import os

from mu.utils import tools

from aml import globals_
from aml import versemaker


class Chapter(object):
    _build_path = "aml/build/chapters"

    sco_name = "notation"
    sf_name = "synthesis"

    def __init__(self, name: str, *verse: versemaker.Verse):
        self._chapter_path = "{}/{}".format(self._build_path, name)
        self._notation_path = "{}/{}/notation".format(self._build_path, name)
        self._name = name
        self._verses = self._sort_verses(verse)

        tools.igmkdir(self.path)
        tools.igmkdir(self.notation_path)

    @classmethod
    def from_path(cls, path: str = "aml/composition/al-hasyr") -> "Chapter":
        name = path.split("/")[-1]

        verses = []
        for fl in os.listdir(path):
            if fl[-2:] == "py":
                local_path = "{}/{}".format(path, fl[:-3])
                module = local_path.replace("/", ".")
                split_position = module.index(".")
                module, relative_path = module[:split_position], module[split_position:]
                verses.append(importlib.import_module(relative_path, module).main())

        return cls(name, *verses)

    @staticmethod
    def _sort_verses(verses: tuple) -> tuple:
        # TODO(implement proper sort verses method!)
        return verses

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

    def _render_verses(self) -> None:
        """Generate notation & sound files for each instrument in each verse."""

        for verse in self.verses:

            verse_path = "{}/{}".format(self.path, verse.verse)
            tools.igmkdir(verse_path)

            for meta_track in globals_.ORCHESTRATION:
                instrument_path = "{}/{}".format(verse_path, meta_track)
                tools.igmkdir(instrument_path)

                track = getattr(verse, meta_track)
                track.notate("{}/{}".format(instrument_path, self.sco_name))
                track.synthesize("{}/{}".format(instrument_path, self.sf_name))

    def _make_notation_for_each_instrument(self) -> None:
        # TODO(implement making a notation png for each instrument using pillow)
        pass

    def __call__(self, render_verses: bool = True) -> None:
        """Generate png file for each instrument."""

        if render_verses:
            self._render_verses()

        self._make_notation_for_each_instrument()
