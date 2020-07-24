import abjad

from mu.mel import ji
from mu.mel import mel
from mu.sco import old

from mutools import lily
from mutools import synthesis

from aml import globals_


def _notate(name: str, instrument: str, scale: tuple) -> None:
    if instrument == "violin":
        clef = abjad.Clef("treble")
        header_distance = -0.4
    elif instrument == "viola":
        clef = abjad.Clef("alto")
        header_distance = -1
    elif instrument == "cello":
        clef = abjad.Clef("bass")
        header_distance = -1
    else:
        raise NotImplementedError(instrument)

    staff = abjad.Staff([])
    for idx, pitch in enumerate(scale):
        abjad_pitch = lily.convert2abjad_pitch(
            pitch, globals_.RATIO2PITCHCLASS
        )
        staff.append(abjad.Note(abjad_pitch, abjad.Duration(1)))

    abjad.attach(lily.mk_no_time_signature(), staff[0])
    abjad.attach(abjad.TimeSignature((len(staff), 1)), staff[0])
    abjad.attach(clef, staff[0])
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
            + " 1/8)",
            format_slot="before",
        ),
        staff[0],
    )

    abjad.attach(
        abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"), staff[0],
    )

    sco = abjad.Score([staff])

    header_block = abjad.Block("header")
    header_block.piece = abjad.Markup(
        abjad.MarkupCommand(
            "center-column",
            [
                abjad.MarkupCommand("fontsize", -1.5),
                abjad.MarkupCommand("smallCaps"),
                "scale for {}".format(instrument),
                abjad.MarkupCommand("vspace", header_distance),
            ],
        )
    )
    lily.make_small_example(
        sco, "{}/pictures/scale_{}".format(name, instrument), header_block=header_block
    )


def _synthezise(name: str, instrument: str, scale: tuple) -> None:
    """make short sound files for string players to get used to intonation"""
    duration_per_tone = 1.5
    rest_duration = 0.75
    melody = old.Melody([])
    for pitch in scale + tuple(reversed(scale))[1:]:
        melody.append(old.Tone(pitch, duration_per_tone))
        melody.append(old.Tone(mel.TheEmptyPitch, rest_duration))

    synth = synthesis.SimpleCsoundSinePlayer(melody)
    # for debugging:
    # synth.remove_files = False
    # synth.print_output = True
    synth.concert_pitch = globals_.CONCERT_PITCH
    synth.render("{}/soundfiles/scale_{}".format(name, instrument))


def _adjust_scale(instrument: int, scale: tuple) -> tuple:
    if instrument == "violin":
        octave = 0
    elif instrument == "viola":
        octave = 0
    elif instrument == "cello":
        octave = -1
    else:
        raise NotImplementedError(instrument)

    adapted_scale = []
    for idx, pitch in enumerate(scale):
        registered_pitch = pitch.register(octave)
        if not idx and instrument == "viola":
            registered_pitch -= ji.r(2, 1)
        adapted_scale.append(registered_pitch)

    return tuple(adapted_scale)


def main(name: str) -> None:
    for instrument, scale in globals_.SCALE_PER_INSTRUMENT.items():
        adapted_scale = _adjust_scale(instrument, scale)
        _notate(name, instrument, adapted_scale)
        _synthezise(name, instrument, adapted_scale)
