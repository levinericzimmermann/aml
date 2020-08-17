import pylatex


def _make_img(path: str, width: float = 1) -> pylatex.Figure:
    graphic = pylatex.Command(
        "includegraphics",
        options=[pylatex.NoEscape("width={}".format(width) + r"\textwidth")],
        arguments=pylatex.NoEscape(path),
    )
    return pylatex.Figure(arguments=graphic, position="H")


def _make_graphics():
    from aml import globals_

    from . import playing_techniques
    from . import scales
    from . import twelfth_tone_accidentals

    playing_techniques.main(globals_.INTRODUCTION_PICTURES_PATH)
    scales.main(globals_.INTRODUCTION_PATH)

    TWELFTH_TONE_EXPLANATION_PATH = "{}/twelfth_tone_explanation".format(
        globals_.INTRODUCTION_PICTURES_PATH
    )

    twelfth_tone_accidentals.main(TWELFTH_TONE_EXPLANATION_PATH)


def make_introduction(make_graphics: bool = False):
    import os

    from aml import globals_

    from mutools import mus

    if make_graphics:
        _make_graphics()

    images = {}
    for iname in os.listdir(globals_.INTRODUCTION_PICTURES_PATH):
        splitted_iname = iname.split(".")
        if splitted_iname[1] == "png":
            ipath = r"{}/{}".format(globals_.INTRODUCTION_PICTURES_PATH, iname)
            images.update({splitted_iname[0]: os.path.realpath(ipath)})

    language_options = {"en": "english", "de": "ngerman"}

    # (2) writing document
    for paper_format in (mus.A4, mus.A3):
        for language in ("de", "en"):
            texts_path = "aml/introduction/texts/{}".format(language)
            texts = {}
            for fname in os.listdir(texts_path):
                subtexts = {}
                for subtext in os.listdir("{}/{}".format(texts_path, fname)):
                    with open("{}/{}/{}".format(texts_path, fname, subtext), "r") as f:
                        subtexts.update({subtext: f.read()})

                texts.update({fname: subtexts})

            path = "{}/introduction_{}_{}".format(
                globals_.INTRODUCTION_PATH, paper_format.name, language
            )
            document = pylatex.Document(default_filepath=path)
            document.packages.remove(pylatex.Package("lastpage"))
            document.packages.append(
                pylatex.Package(
                    "geometry",
                    options=[
                        "{}paper".format(paper_format.name),
                        "bindingoffset=0.2in",
                        "left=0.8cm",
                        "right=1cm",
                        "top=1cm",
                        "bottom=1cm",
                        "footskip=.25in",
                    ],
                )
            )
            document.packages.append(pylatex.Package("microtype"))
            document.packages.append(pylatex.Package("float"))
            document.packages.append(pylatex.Package("graphicx"))
            document.packages.append(pylatex.Package("fancyhdr"))
            document.packages.append(
                pylatex.Package("setspace", options=['onehalfspacing'])
            )
            document.packages.append(
                pylatex.Package("babel", options=[language_options[language]])
            )

            document.preamble.append(
                pylatex.NoEscape(r"\fancyhf{} % clear all header and footers")
            )
            document.preamble.append(
                pylatex.NoEscape(r"\setlength{\parindent}{0pt}")
            )

            # suppress page number
            document.preamble.append(
                pylatex.NoEscape(r"\pagenumbering{gobble}")
            )
            document.preamble.append(
                pylatex.NoEscape(r"\linespread{1.213}")
            )

            document.append(
                pylatex.Section(
                    title=texts["title"]["title"], label=False, numbering=False
                )
            )

            ###################################################################
            #   general remarks regarding setup and compositoon               #
            ###################################################################

            document.append(
                pylatex.Subsection(
                    title=texts["setup"]["title"],
                    label=False,
                    numbering=False,
                )
            )

            document.append(_make_img(images["stage-setup"], width=0.8))

            ###################################################################
            #   remarks and notes for keyboard player                         #
            ###################################################################

            document.append(
                pylatex.Subsection(
                    title=texts["keyboard"]["title"],
                    label=False,
                    numbering=False,
                )
            )

            ###################################################################
            #   remarks and notes for string player                           #
            ###################################################################

            document.append(
                pylatex.Subsection(
                    title=texts["strings"]["title"],
                    label=False,
                    numbering=False,
                )
            )

            document.append(
                pylatex.Subsubsection(
                    title=texts["strings"]["subtitle0"],
                    label=False,
                    numbering=False,
                )
            )

            document.append(texts["strings"]["text0"])

            document.append(
                pylatex.Subsubsection(
                    title=texts["microtonal_notation"]["title"],
                    label=False,
                    numbering=False,
                )
            )
            document.append(texts["microtonal_notation"]["text0"])
            document.append(_make_img(images["twelfth_tone_explanation"]))

            document.append(texts["microtonal_notation"]["text1"])

            for instrument in ("violin", "viola", "cello"):
                document.append(_make_img(images["scale_{}".format(instrument)]))
                document.append(
                    _make_img(
                        images["scale_{}_artificial_harmonics".format(instrument)]
                    )
                )
                document.append(pylatex.Command('hspace', arguments=[pylatex.NoEscape('5mm')]))

            document.append(texts["microtonal_notation"]["text2"])

            document.append(
                pylatex.Subsubsection(
                    title=texts["strings"]["subtitle1"],
                    label=False,
                    numbering=False,
                )
            )
            document.append(_make_img(images["ornamentation"], width=0.25))
            document.append(texts["strings"]["text1"])

            document.append(_make_img(images["glissando"], width=0.28))

            document.append(texts["strings"]["text2"])

            print("gen doc {}".format(path))
            document.generate_pdf()
