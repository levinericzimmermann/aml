import abjad

from mu.mel import ji
from mu.mel import mel
from mu.sco import old
from mu.utils import tools

from mutools import lily
from mutools import synthesis

from aml import globals_


def _notate(name: str, instrument: str, scale: tuple) -> None:
    for add_harmonics in (False, True):
        if add_harmonics:
            harmonics_dict = {
                key: value[0]
                for key, value in globals_.RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE.items()
            }

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
            abjad_pitch = lily.convert2abjad_pitch(pitch, globals_.RATIO2PITCHCLASS)

            if add_harmonics:
                (
                    _,
                    octave,
                ) = globals_.RATIO2ARTIFICAL_HARMONIC_PITCHCLASS_AND_ARTIFICIAL_HARMONIC_OCTAVE[
                    pitch.register(0)
                ]
                harmonic_pitch = lily.convert2abjad_pitch(
                    pitch + ji.JIPitch([octave]), harmonics_dict
                )
                chord = abjad.Chord(
                    sorted([abjad_pitch, harmonic_pitch]), abjad.Duration(1)
                )
                abjad.tweak(chord.note_heads[1]).style = "harmonic"
                staff.append(chord)
            else:
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

        if add_harmonics:
            descr = "scale for {} with artifical harmonics".format(instrument)
        else:
            descr = "scale for {}".format(instrument)

        header_block = abjad.Block("header")
        header_block.piece = abjad.Markup(
            abjad.MarkupCommand(
                "center-column",
                [
                    abjad.MarkupCommand("fontsize", -1.5),
                    abjad.MarkupCommand("smallCaps"),
                    descr,
                    abjad.MarkupCommand("vspace", header_distance),
                ],
            )
        )
        final_file_name = "{}/pictures/scale_{}".format(name, instrument)

        if add_harmonics:
            final_file_name = "{}_artifical_harmonics".format(final_file_name)

        lily.make_small_example(sco, final_file_name, header_block=header_block)


def _synthezise(name: str, instrument: str, scale: tuple) -> None:
    """make short sound files for string players to get used to intonation"""

    # (1) generate file where scale get played up & down
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
    synth.render("{}/soundfiles/wav/scale_{}".format(name, instrument))

    instrument_path = "{}/soundfiles/wav/{}".format(name, instrument)
    tools.igmkdir(instrument_path)

    # (2) generate for each scale degree one file
    single_tone_duration = 3
    duration_per_tone_rest_duration = 0.75
    for idx, pitch in enumerate(scale):
        melody = old.Melody(
            [
                old.Tone(pitch, single_tone_duration),
                old.Tone(mel.TheEmptyPitch, duration_per_tone_rest_duration),
            ]
        )
        synth = synthesis.SimpleCsoundSinePlayer(melody)
        synth.concert_pitch = globals_.CONCERT_PITCH
        synth.render("{}/{}".format(instrument_path, idx + 1))


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
