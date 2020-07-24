import fractions

import abjad

from mutools import lily


def main(name: str, ignore_accidentals_higher_than_semitone: bool = True) -> None:
    pitch = 7
    note_duration = fractions.Fraction(1, 1)

    staff = []
    for nth in range(23):
        diff_written = fractions.Fraction(nth - 11, 12)
        diff_true = fractions.Fraction(nth - 11, 6)

        note = abjad.Note(abjad.NamedPitch(pitch + diff_true), note_duration)

        if diff_written == 0:
            marking = None
        else:
            marking = "{}/{}".format(diff_written.numerator, diff_written.denominator)
            marking = abjad.MarkupCommand(
                "fraction {} {}".format(
                    abs(diff_written.numerator), diff_written.denominator
                )
            )
            if diff_written > 0:
                prefix = "+"
            else:
                prefix = "-"

        if marking:
            markup = abjad.Markup(
                [abjad.MarkupCommand("abs-fontsize", 8, [prefix, marking])],
                direction="up",
            )
            abjad.attach(markup, note)

        staff.append(note)

        if nth == 11:
            abjad.Accidental.respell_with_flats(staff)

    abjad.Accidental.respell_with_sharps(staff[17:])

    if ignore_accidentals_higher_than_semitone:
        staff = staff[5:18]

    staff = abjad.Staff(staff)

    abjad.attach(lily.mk_no_time_signature(), staff[0])
    abjad.attach(abjad.TimeSignature((len(staff), 1)), staff[0])
    abjad.attach(
        abjad.LilyPondLiteral(
            "\\override Score.SpacingSpanner.strict-note-spacing = ##t",
            format_slot="before",
        ),
        staff[0],
    )
    abjad.attach(
        abjad.LilyPondLiteral("\\newSpacingSection", format_slot="before"), staff[0]
    )
    abjad.attach(
        abjad.LilyPondLiteral(
            "\\override Score.SpacingSpanner.base-shortest-duration = #(ly:make-moment"
            + " 1/16)",
            format_slot="before",
        ),
        staff[0],
    )

    sco = abjad.Score([staff])

    header_block = abjad.Block("header")
    header_block.piece = abjad.Markup(
        abjad.MarkupCommand(
            "center-column",
            [
                abjad.MarkupCommand("fontsize", -1.5),
                abjad.MarkupCommand("smallCaps"),
                "12-tone accidentals",
                abjad.MarkupCommand("vspace", -0.35),
            ],
        )
    )
    lily.make_small_example(sco, name, header_block=header_block)
