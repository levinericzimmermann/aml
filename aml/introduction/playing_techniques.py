import abjad

from mutools import attachments
from mutools import lily


def _notate_ornamentation(name: str) -> None:
    staff = abjad.Staff([abjad.Note("a'", 0.5), abjad.Note("f'", 0.5)])

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
            + " 1/32)",
            format_slot="before",
        ),
        staff[0],
    )

    abjad.attach(lily.mk_no_time_signature(), staff[0])
    abjad.attach(abjad.TimeSignature((len(staff), 1)), staff[0])
    abjad.attach(abjad.Clef("treble"), staff[0])
    abjad.attach(attachments.OrnamentationUp(2)._markup, staff[0])
    abjad.attach(attachments.OrnamentationDown(3)._markup, staff[1])

    sco = abjad.Score([staff])
    lily.make_small_example(sco, name, ragged_last=True, ragged_right=True)


def _notate_glissando(name: str) -> None:
    staff = abjad.Staff(
        [
            abjad.Note("a'", 3 / 16),
            abjad.Note("a'", 1 / 16),
            abjad.Note("a'", 1 / 8),
            abjad.Note("a'", 1 / 8),
        ]
    )

    abjad.attach(
        abjad.LilyPondLiteral("#(define afterGraceFraction (cons 15 16))"), staff[0]
    )
    abjad.attach(
        abjad.LilyPondLiteral('\\override Flag.stroke-style = #"grace"'), staff[0],
    )

    for n in (0, 2):
        attachments._GlissandoAttachment._set_glissando_layout(
            staff[n + 1], minimum_length=3
        )
        abjad.attach(abjad.AfterGraceContainer([abjad.Note("f'", 1 / 8)]), staff[n + 1])
        abjad.attach(abjad.Tie(), staff[n])
        abjad.attach(abjad.StartBeam(), staff[n])
        abjad.attach(abjad.StopBeam(), staff[n + 1])
        abjad.attach(abjad.GlissandoIndicator(), staff[n + 1])

    abjad.attach(lily.mk_no_time_signature(), staff[0])
    abjad.attach(abjad.TimeSignature((len(staff), 1)), staff[0])
    abjad.attach(abjad.Clef("treble"), staff[0])

    sco = abjad.Score([staff])
    lily.make_small_example(sco, name, ragged_last=True, ragged_right=True)


def main(name: str) -> None:
    _notate_ornamentation("{}/ornamentation".format(name))
    _notate_glissando("{}/glissando".format(name))
