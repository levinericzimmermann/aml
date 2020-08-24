"""General script for the generation of each instruments partbook."""

import PyPDF2

from mutools import mus

from aml import globals_


def _make_basic_document(paper_format: mus.PaperFormat) -> PyPDF2.PdfFileMerger:
    merger = PyPDF2.PdfFileMerger()
    merger.append("{}/cover_{}.pdf".format(globals_.COVER_PATH, paper_format.name))
    # for language in ("de", "en"):  # english remarks aren't finished yet
    for language in ("de",):
        merger.append(
            "{}/introduction_{}_{}.pdf".format(
                globals_.INTRODUCTION_PATH, paper_format.name, language
            )
        )
    return merger


def make(chapters: tuple) -> None:
    for paper_format in (mus.A4, mus.A3):
        for instrument in (None,) + tuple(iter(globals_.ORCHESTRATION)):
            merger = _make_basic_document(paper_format)
            simplified_title = "".join(chapters[0].title.split(" "))

            for chapter in chapters:
                chapter_notation_path = "{}/full_score".format(chapter.notation_path)
                if instrument:
                    chapter_notation_path = "{}/{}/{}.pdf".format(
                        chapter_notation_path, paper_format.name, instrument
                    )
                else:
                    chapter_notation_path = "{}/{}_{}.pdf".format(
                        chapter_notation_path, simplified_title, paper_format.name
                    )

                merger.append(chapter_notation_path)

            if instrument:
                output_path = "{}/{}/{}_{}_{}.pdf".format(
                    globals_.PARTBOOKS_PATH,
                    paper_format.name,
                    simplified_title,
                    paper_format.name,
                    instrument,
                )
            else:
                output_path = "{}/{}_{}.pdf".format(
                    globals_.SCORE_PATH,
                    paper_format.name,
                    simplified_title,
                    paper_format.name,
                )

            merger.write(output_path)
