import importlib
import os

import PIL

import abjad

from mu.utils import tools

from mutools import lily
from mutools import mus

from aml import globals_
from aml import versemaker


class Chapter(object):
    _build_path = "aml/build/chapters"

    sco_name = "notation"
    sf_name = "synthesis"

    make_png = False
    _orientation_staff_size = -4

    def __init__(self, name: str, *verse: versemaker.Verse, title: str = None):
        self._chapter_path = "{}/{}".format(self._build_path, name)
        self._notation_path = "{}/{}/notation".format(self._build_path, name)
        self._name = name
        self._title = title
        self._verses = self._sort_verses(verse)

        tools.igmkdir(self.path)
        tools.igmkdir(self.notation_path)

    @property
    def title(self) -> str:
        return self._title

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

    def _render_verses(
        self, render_each_track: bool = True, render_notation: bool = True
    ) -> None:
        """Generate notation & sound files for each instrument in each verse."""
        notation_processes = []
        for verse in self.verses:

            verse_path = "{}/{}".format(self.path, verse.verse)
            tools.igmkdir(verse_path)

            verse.synthesize(verse_path, self.sf_name, render_each_track)
            if render_notation:
                verse.notate("{}/{}".format(verse_path, self.sco_name))

            for meta_track in globals_.ORCHESTRATION:
                instrument_path = "{}/{}".format(verse_path, meta_track)
                tools.igmkdir(instrument_path)

                track = getattr(verse, meta_track)
                if self.make_png:
                    notation_processes.append(
                        track.notate("{}/{}".format(instrument_path, self.sco_name))
                    )

                if meta_track == "keyboard":
                    # for the purpose of simulation live electronics
                    track.make_midi_file(
                        "{}/keyboard_simulation".format(instrument_path)
                    )

        for process in notation_processes:
            process.wait()

    def _make_png_notation_for_each_instrument(self) -> None:
        A2_inches = (23.4, 16.5)
        A2_pixel = tuple(int(inch * mus.STANDARD_RESOLUTION) for inch in A2_inches)

        distance_width = 0.25  # inches
        distance_width = int(distance_width * mus.STANDARD_RESOLUTION)

        for meta_track in globals_.ORCHESTRATION:
            notation_path = "{}/notation/with_orientation/{}.pdf".format(
                self.path, meta_track
            )
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
            notation_path = "{}/notation/with_orientation/{}".format(
                self.path, meta_track
            )
            is_first = True
            for verse in self.verses:
                track = getattr(verse, meta_track)
                track.indent_first = False
                if is_first:
                    lpf = track._make_lilypond_file()
                    is_first = False
                else:
                    lpf.items.append(track._make_score_block())

            if self._title:
                lpf.header_block.title = abjad.Markup(self._title)

            track._notate(notation_path, lpf)

    @staticmethod
    def _detach_optional_tone_tweaks(staff: abjad.Staff) -> None:
        for bar in staff:
            for obj in bar:
                abjad.detach(abjad.LilyPondLiteral("\\once \\tiny"), obj)
                if type(obj) == abjad.Chord:
                    for note_head in obj.note_heads:
                        if hasattr(note_head.tweaks, "font_size"):
                            del note_head.tweaks.font_size

    def _make_full_score_pdf_notation_for_each_instrument(self) -> None:
        for paper_format in (mus.A3, mus.A4):
            for meta_track in globals_.ORCHESTRATION:
                notation_path = "{}/notation/full_score/{}/{}".format(
                    self.path, paper_format.name, meta_track
                )
                is_first = True
                for verse in self.verses:
                    track = getattr(verse, meta_track)
                    track.format = paper_format
                    if is_first:
                        track.indent_first = True
                        track.global_staff_size = 20
                        lpf = track._make_lilypond_file(make_layout_block_global=False)

                    else:
                        track.indent_first = False
                        lpf.items.append(
                            track._make_score_block(make_layout_block=True)
                        )

                    last_score_block = lpf.items[-1]

                    instr_staff = abjad.mutate(last_score_block.items[0][0][1]).copy()
                    instr_obj = globals_.INSTRUMENT_NAME2OBJECT[meta_track]

                    if is_first:
                        abjad.setting(instr_staff).instrument_name = instr_obj.markup

                    else:
                        abjad.setting(
                            instr_staff
                        ).instrument_name = instr_obj.short_markup

                    abjad.setting(
                        instr_staff
                    ).short_instrument_name = instr_obj.short_markup
                    last_score_block.items[0] = abjad.Score([instr_staff])

                    for other_meta_track in reversed(
                        tuple(iter(globals_.ORCHESTRATION))
                    ):
                        if meta_track != other_meta_track:
                            other_track = getattr(verse, other_meta_track)
                            new_staff = abjad.mutate(other_track.score[0][1]).copy()
                            if type(new_staff) == abjad.StaffGroup:
                                for sub_staff in new_staff:
                                    self._detach_optional_tone_tweaks(sub_staff)
                            else:
                                self._detach_optional_tone_tweaks(new_staff)

                            instr_obj = globals_.INSTRUMENT_NAME2OBJECT[
                                other_meta_track
                            ]
                            abjad.setting(
                                new_staff
                            ).font_size = self._orientation_staff_size
                            magstep = abjad.Scheme(
                                ["magstep", self._orientation_staff_size]
                            )
                            abjad.override(new_staff).staff_symbol.thickness = magstep
                            abjad.override(new_staff).staff_symbol.staff_space = magstep

                            if is_first:
                                instrument_name_markup = instr_obj.name
                            else:
                                instrument_name_markup = instr_obj.short_name

                            instrument_name_markup = (
                                instrument_name_markup[0].capitalize()
                                + instrument_name_markup[1:].lower()
                            )

                            if is_first:
                                short_instrument_name_markup = instr_obj.short_name
                                short_instrument_name_markup = (
                                    short_instrument_name_markup[0].capitalize()
                                    + short_instrument_name_markup[1:].lower()
                                )
                            else:
                                short_instrument_name_markup = instrument_name_markup

                            if other_meta_track == "keyboard":
                                instrument_name_markup = abjad.Markup(
                                    [
                                        abjad.MarkupCommand(
                                            "fontsize", self._orientation_staff_size
                                        ),
                                        instrument_name_markup,
                                    ]
                                )
                                short_instrument_name_markup = abjad.Markup(
                                    [
                                        abjad.MarkupCommand(
                                            "fontsize", self._orientation_staff_size
                                        ),
                                        short_instrument_name_markup,
                                    ]
                                )

                            else:
                                instrument_name_markup = abjad.Markup(
                                    instrument_name_markup
                                )
                                short_instrument_name_markup = abjad.Markup(
                                    short_instrument_name_markup
                                )

                            abjad.setting(
                                new_staff
                            ).instrument_name = instrument_name_markup
                            abjad.setting(
                                new_staff
                            ).short_instrument_name = short_instrument_name_markup
                            last_score_block.items[0].insert(0, new_staff)

                        else:
                            copied_staff = abjad.mutate(last_score_block.items[0][-1]).copy()
                            del last_score_block.items[0][-1]
                            last_score_block.items[0].insert(0, copied_staff)

                    is_first = False

                if self._title:
                    lpf.header_block.title = abjad.Markup(self._title)

                track._notate(notation_path, lpf)

    @staticmethod
    def _set_instrument_name(
        instr_staff: abjad.Staff, instr_obj: abjad.Instrument, is_first_verse: bool
    ) -> None:
        if is_first_verse:
            abjad.setting(instr_staff).instrument_name = instr_obj.markup
        else:
            abjad.setting(instr_staff).instrument_name = instr_obj.short_markup

        abjad.setting(instr_staff).short_instrument_name = instr_obj.short_markup

    def _make_full_score_pdf_notation(self) -> None:
        for paper_format in (mus.A3, mus.A4):
            is_first_verse = True
            notation_path = "{}/notation/full_score/{}_{}".format(
                self.path, self._title.replace(" ", ""), paper_format.name
            )
            for verse in self.verses:
                is_first_track = True
                for meta_track in globals_.ORCHESTRATION:
                    track = getattr(verse, meta_track)
                    track.format = paper_format
                    if (is_first_verse and is_first_track) or is_first_track:
                        if is_first_verse:
                            track.indent_first = True
                            track.global_staff_size = 15
                            lpf = track._make_lilypond_file(
                                make_layout_block_global=False
                            )

                        else:
                            track.indent_first = False
                            lpf.items.append(
                                track._make_score_block(make_layout_block=True)
                            )

                        last_score_block = lpf.items[-1]

                        instr_staff = abjad.mutate(
                            last_score_block.items[0][0][1]
                        ).copy()
                        instr_obj = globals_.INSTRUMENT_NAME2OBJECT[meta_track]
                        self._set_instrument_name(
                            instr_staff, instr_obj, is_first_verse
                        )
                        last_score_block.items[0] = abjad.Score([instr_staff])

                    else:
                        last_score_block = lpf.items[-1]

                        instr_staff = abjad.mutate(track.score[0][1]).copy()
                        instr_obj = globals_.INSTRUMENT_NAME2OBJECT[meta_track]
                        self._set_instrument_name(
                            instr_staff, instr_obj, is_first_verse
                        )
                        last_score_block.items[0].append(instr_staff)

                    is_first_track = False

                is_first_verse = False

            if self._title:
                lpf.header_block.title = abjad.Markup(self._title)

            lily.write_lily_file(lpf, notation_path)
            lily.render_lily_file(
                notation_path,
                write2png=False,
                resolution=None,
                output_name=notation_path,
            )

    def _make_notation_for_each_instrument(self) -> None:
        if self.make_png:
            self._make_png_notation_for_each_instrument()
        else:
            self._make_full_score_pdf_notation_for_each_instrument()
            self._make_pdf_notation_for_each_instrument()

    def __call__(
        self,
        render_verses: bool = True,
        render_notation_of_verses: bool = False,
        render_each_instrument: bool = True,
    ) -> None:
        """Generate png file for each instrument."""

        self._make_full_score_pdf_notation()

        if render_verses:
            self._render_verses(
                render_each_instrument, render_notation=render_notation_of_verses
            )

        self._make_notation_for_each_instrument()
