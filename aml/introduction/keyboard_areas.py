import abjad

from mutools import lily

from aml.trackmaker import keyboard


def main(name: str) -> None:
    for idx, clef, zone in zip(
        range(3),
        (abjad.Clef("bass_15"), abjad.Clef("bass"), abjad.Clef("treble^8")),
        keyboard.ZONES,
    ):

        staff = abjad.Staff([])
        for pitch in (zone[0], zone[1] - 1):
            staff.append(abjad.Note(pitch - 60, 1))  # midi pitch 60 is abjad pitch 0

        abjad.attach(lily.mk_no_time_signature(), staff[0])
        abjad.attach(abjad.TimeSignature((len(staff), 1)), staff[0])
        abjad.attach(clef, staff[0])
        abjad.attach(abjad.GlissandoIndicator(), staff[0])

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
                "\\override Score.SpacingSpanner.base-shortest-duration ="
                " #(ly:make-moment"
                + " 1/8)",
                format_slot="before",
            ),
            staff[0],
        )

        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"), staff[0],
        )

        sco = abjad.Score([staff])
        lily.make_small_example(
            sco, "{}/zone_{}".format(name, idx), ragged_right=True, ragged_last=True
        )
