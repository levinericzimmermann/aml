import functools
import json
import operator
import subprocess

import abjad
import quicktions as fractions

from mu.mel import ji
from mu.sco import old
from mu.utils import infit
from mu.utils import tools

from mutools import attachments
from mutools import mus
from mutools import lily
from mutools import synthesis

from aml import comprovisation
from aml import globals_

KEYBOARD_SETUP_PATH = "aml/keyboard_setups"


LOWEST_MIDI_NOTE = 23  # starting from b, so that each zone is repeating at each new b
N_MIDI_NOTES_PER_ZONE = (12, 3 * 12, 3 * 12)  # 1 octave, 3 octaves, 3 octaves


def _make_keyboard_zones() -> tuple:
    accumulated_zones = tools.accumulate_from_n(N_MIDI_NOTES_PER_ZONE, LOWEST_MIDI_NOTE)
    return tuple(zip(accumulated_zones, accumulated_zones[1:]))


ZONES = _make_keyboard_zones()


def _generate_keyboard_midi_note2ji_pitch_mapping():
    # each intonation is allowed to appear twice in each zone (pianoteq and sine waves).
    # the following tuple assigns in which register each intonation of one scale degree
    # will appear (3 subtuples because there are always three different intonations per
    # scale degree). each subtuple contains again two tuples. the first tuple contains
    # integer representing the register for the pianoteq-zone and the second tuple
    # contains integer representing the register for the sine-wave-zone of this
    # intonation.the order of the distribution is depending on how frequent the particular
    # intonation is globally appearing in the transcription of the recitation where the
    # first entry is reserved for the most frequent appearing intonation.
    distributed_register_for_scale_pitches = (
        ((-1, 0), (0, 1)),  # most frequent intonation
        ((-2, -1), (-1, 0)),  # second frequent intonation
        ((-2, 0), (-1, 1)),  # least frequent intonation
    )

    # each auxiliary pitch intonation is only allowed to appear once in each zone.
    # the following tuple contains 3 subtuples that indicate the register for this
    # particular intonation within the pianoteq (first entry) and the sine-wave zone
    # (second entry). the individual subtuples aren't sorted in any particular way.
    distributed_register_for_auxiliary_pitches = (
        ((0,), (-1,)),
        ((-1,), (0,)),
        ((-2,), (1,)),
    )

    # where 0 is b, 1 is c, ...
    available_chromatic_pitches_per_scale_degree = (
        (0, 1),  # 1
        (2, 3),  # 2
        (4, 5),  # 3
        (6,),  # 4 -> only one scale degree because 4 is an auxiliary pitch
        (7, 8),  # 5
        (9, 10),  # 6
        (11,),  # 7 -> only one scale degree because 7 is an auxiliary pitch
    )

    with open("aml/counted_intonations_in_all_transcriptions.json", "r") as f:
        counted_intonations_in_all_transcriptions = json.load(f)

    # the pianoteq zone contains pitches from B to b'
    # the sine wave zone contains pitches from b to b''
    available_register_per_zone = ((-2, -1, 0), (-1, 0, 1))

    midi_note2ji_pitch_mapping_per_zone = {
        "pianoteq": {mn: None for mn in range(*ZONES[1])},
        "sine": {mn: None for mn in range(*ZONES[2])},
    }

    for intonations, available_chromatic_pitches, frequency_per_intonation in zip(
        globals_.INTONATIONS_PER_SCALE_DEGREE,
        available_chromatic_pitches_per_scale_degree,
        counted_intonations_in_all_transcriptions,
    ):
        if len(available_chromatic_pitches) == 2:
            sorted_frequency_per_intonation = sorted(
                frequency_per_intonation, reverse=True
            )
            distribution_per_intonation = tuple(
                distributed_register_for_scale_pitches[
                    sorted_frequency_per_intonation.index(frequency)
                ]
                for frequency in frequency_per_intonation
            )

        else:
            distribution_per_intonation = distributed_register_for_auxiliary_pitches

        available_positions_per_octave_per_zone = tuple(
            tuple(
                tuple(
                    chromatic_pitch + (12 * n) + zone_start
                    for chromatic_pitch in available_chromatic_pitches
                )
                for n in range(len(available_register))
            )
            for zone_start, available_register in zip(
                (ZONES[1][0], ZONES[2][0]), available_register_per_zone
            )
        )

        available_pitches_per_octave_per_zone = [
            [[] for register in available_register]
            for available_register in available_register_per_zone
        ]

        for intonation, distribution in zip(intonations, distribution_per_intonation):
            for zone_idx, available_register_in_this_zone in enumerate(distribution):
                for register in available_register_in_this_zone:
                    register_idx = available_register_per_zone[zone_idx].index(register)
                    registered_pitch = intonation + ji.r(1, 1).register(register)
                    available_pitches_per_octave_per_zone[zone_idx][
                        register_idx
                    ].append(registered_pitch)

        for (
            zone_name,
            available_pitches_per_octave,
            available_positions_per_octave,
        ) in zip(
            ("pianoteq", "sine"),
            available_pitches_per_octave_per_zone,
            available_positions_per_octave_per_zone,
        ):
            for available_pitches, available_positions in zip(
                available_pitches_per_octave, available_positions_per_octave
            ):
                for position, pitch in zip(
                    available_positions, sorted(available_pitches)
                ):
                    midi_note2ji_pitch_mapping_per_zone[zone_name][position] = pitch

    return midi_note2ji_pitch_mapping_per_zone


MIDI_NOTE2JI_PITCH_PER_ZONE = _generate_keyboard_midi_note2ji_pitch_mapping()


def _generate_keyboard_mapping_files():
    def gen_right_hand_mapping():
        _right_hand_mapping_path = "{}/midi_note2freq_and_instrument_mapping.json".format(
            KEYBOARD_SETUP_PATH
        )

        data = {
            midi_note: (
                float(jipitch) * globals_.CONCERT_PITCH,
                globals_.PITCH2INSTRUMENT[jipitch.normalize()],
            )
            for midi_note, jipitch in MIDI_NOTE2JI_PITCH_PER_ZONE["sine"].items()
        }
        with open(_right_hand_mapping_path, "w") as f:
            json.dump(data, f)

    def gen_left_hand_mapping():
        # generate scl file ... kbm file has been written by hand and has to adapted
        # manually in case of any significant change
        scl_f_name = "pteq.scl"
        _left_hand_mapping_path = "{}/{}".format(KEYBOARD_SETUP_PATH, scl_f_name)

        rising_pitches = tuple(sorted(MIDI_NOTE2JI_PITCH_PER_ZONE["pianoteq"].values()))
        first_ct = rising_pitches[0].cents
        cent_values = tuple(p.cents - first_ct for p in rising_pitches[1:]) + (3600,)
        with open(_left_hand_mapping_path, "w") as f:
            f.write(
                "\n".join(
                    (
                        "! {}".format(scl_f_name),
                        "!",
                        " 21 pitches uneven distributed on 3 octaves.",
                        " 36",
                        "!\n",
                    )
                )
            )
            for ct in cent_values:
                f.write("{}\n".format(ct))

    gen_right_hand_mapping()
    gen_left_hand_mapping()


_generate_keyboard_mapping_files()


KEYBOARD_RATIO2PITCH_PER_ZONE = {
    zone_name: {
        ratio: globals_.MIDI_PITCH2ABJAD_PITCH[midi_note]
        for midi_note, ratio in zone.items()
    }
    for zone_name, zone in MIDI_NOTE2JI_PITCH_PER_ZONE.items()
}


class Keyboard(mus.Track):
    def __init__(
        self,
        abjad_data: abjad.StaffGroup,
        sound_engine: synthesis.SoundEngine,
        resolution: int = None,
    ):
        abjad.attach(
            abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic", "before"),
            abjad_data[0][0][0],
        )

        for staff in abjad_data[1:]:
            abjad.attach(
                abjad.LilyPondLiteral("\\accidentalStyle dodecaphonic-first", "before"),
                staff[0][0],
            )

        abjad_data = abjad.Container(
            [
                abjad.mutate(abjad_data[0]).copy(),
                abjad.StaffGroup([abjad.mutate(d).copy() for d in abjad_data[1:]]),
            ]
        )
        abjad_data.simultaneous = True

        abjad.attach(
            abjad.LilyPondLiteral("\\magnifyStaff #4/7", "before"), abjad_data[0][0][0]
        )
        abjad.attach(abjad.Clef("bass"), abjad_data[1][1][0][0])

        super().__init__(abjad_data, sound_engine, resolution)


class LeftHandKeyboardEngine(synthesis.PyteqEngine):
    def __init__(self, novent_line: lily.NOventLine):
        self._novent_line = comprovisation.process_comprovisation_attachments(
            novent_line
        )
        super().__init__(
            # fxp="aml/keyboard_setups/fxp/VibraphoneV-BHumanizednostretching.fxp"
            # preset='"Erard Player"'
            preset='"Concert Harp Daily"'
        )

    @property
    def CONCERT_PITCH(self) -> float:
        return globals_.CONCERT_PITCH

    def render(self, name: str) -> subprocess.Popen:
        return super().render(name, self._novent_line)


class SilentKeyboardMaker(mus.TrackMaker):
    _track_class = Keyboard

    @staticmethod
    def _prepare_staves(
        polyline: old.PolyLine, segment_maker: mus.SegmentMaker
    ) -> old.PolyLine:
        polyline[1][0].margin_markup = attachments.MarginMarkup(
            "{}.{}".format(segment_maker.chapter, segment_maker.verse),
            context="StaffGroup",
        )

        for nol in polyline:
            nol[0].tempo = attachments.Tempo((1, 4), segment_maker.tempo)

        return old.PolyLine(polyline)

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        return self._prepare_staves(pl, segment_maker)

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return synthesis.SilenceEngine(1)


class KeyboardMaker(SilentKeyboardMaker):
    def __init__(
        self,
        n_beats_per_bar: infit.InfIt = infit.Cycle((4, 3, 5, 4)),
        grid_size: fractions.Fraction = fractions.Fraction(1, 8),
    ):
        self.n_beats_per_bar = n_beats_per_bar
        self.grid_size = grid_size

    @classmethod
    def _convert_mu_pitch2named_pitch(
        cls, pitch: ji.JIPitch, ratio2pitch_class_dict: dict
    ) -> abjad.NamedPitch:
        """somewhat complicated because the same ratio could appear in the left hand and
        also in the right hand"""
        pass

    @staticmethod
    def _sort_orientation_note_pitches(
        previous_pitches: tuple, harmonic_field: dict, available_instruments: tuple
    ) -> tuple:
        available_pitches = functools.reduce(
            operator.add,
            (
                globals_.INSTRUMENT_NAME2ADAPTED_INSTRUMENT[name].scale
                for name in available_instruments
            ),
        )
        pitches_sorted_by_harmonicity = tuple(
            map(
                operator.itemgetter(0),
                sorted(
                    (
                        (p, harmonicity)
                        for p, harmonicity in harmonic_field.items()
                        if p.normalize() in available_pitches
                    ),
                    key=operator.itemgetter(1),
                    reverse=True,
                ),
            )
        )
        pitches_in_sd_3_and_6 = tuple(
            p
            for p in pitches_sorted_by_harmonicity
            if globals_.PITCH2SCALE_DEGREE[p] in (3, 6)
        )
        if previous_pitches:
            pitches_appearing_in_previous_pitches = tuple(
                p for p in pitches_sorted_by_harmonicity if p in previous_pitches
            )
        else:
            pitches_appearing_in_previous_pitches = tuple([])

        pitches = tuple(
            p
            for p in pitches_sorted_by_harmonicity
            if p not in pitches_in_sd_3_and_6 + pitches_appearing_in_previous_pitches
        )
        pitches += pitches_in_sd_3_and_6
        pitches += pitches_appearing_in_previous_pitches
        return pitches

    def _attach_left_hand_orientation_notes(
        self, nset: lily.NOventSet, segment_maker: mus.SegmentMaker
    ) -> None:
        # add mandatory rhythmical / metrical orientation notes
        spread_metrical_loop = segment_maker.transcription.spread_metrical_loop
        rhythm_metricity_pairs = spread_metrical_loop.get_all_rhythm_metricitiy_pairs()
        orientation_rhythm_metricity_pairs = tuple(
            rhythm_metricity_pairs[idx]
            for idx in segment_maker.rhythmic_orientation_indices
        )
        orientation_metricities = tuple(
            map(operator.itemgetter(1), orientation_rhythm_metricity_pairs)
        )
        sorted_orientation_metricities = sorted(set(orientation_metricities))
        n_sorted_orientation_metricities = len(sorted_orientation_metricities)
        scaled_orientation_metricities = tuple(
            sorted_orientation_metricities.index(metricity)
            / n_sorted_orientation_metricities
            for metricity in orientation_metricities
        )

        previous_pitches = None

        for data, next_start in zip(
            orientation_rhythm_metricity_pairs,
            tuple(map(operator.itemgetter(0), orientation_rhythm_metricity_pairs))[1:]
            + (segment_maker.duration,),
        ):
            absolute_position, metricity = data
            primes = spread_metrical_loop.get_primes_of_absolute_rhythm(
                absolute_position
            )
            slice_idx = segment_maker.bread.find_indices_of_responsible_slices(
                absolute_position, absolute_position + 1
            )[0]
            slice_ = segment_maker.bread[slice_idx]

            available_instruments = tuple(
                spread_metrical_loop.prime_instrument_mapping[prime] for prime in primes
            )
            pitches = self._sort_orientation_note_pitches(
                previous_pitches, slice_.harmonic_field, available_instruments
            )
            pitches = pitches[:2]

            previous_pitches = pitches

            for loc_slice_ in segment_maker.bread[slice_idx:]:
                slice_pitches = slice_.harmonic_field.keys()
                if all(tuple(p in slice_pitches for p in pitches)):
                    stop = loc_slice_.stop
                else:
                    break

            stop = min((stop, next_start))
            pitches = tuple(p.register(-1) for p in pitches)
            nevent = lily.NOvent(pitch=pitches, delay=absolute_position, duration=stop)

            scaled_metricity = scaled_orientation_metricities[
                orientation_metricities.index(metricity)
            ]

            if scaled_metricity > 0.66:
                if scaled_metricity > 0.8:
                    nevent.articulation_once = attachments.ArticulationOnce("accent")
                    nevent.volume = 0.8

                nevent.volume = 0.7

            elif scaled_metricity > 0.33:
                if len(pitches) > 1:
                    nevent.choose = attachments.Choose()
                nevent.volume = 0.6

            else:
                if len(pitches) > 1:
                    nevent.choose = attachments.ChooseOne()
                nevent.volume = 0.5

            nset.append(nevent)

    def _make_left_hand(self, segment_maker: mus.SegmentMaker) -> lily.NOventLine:
        nset = lily.NOventSet(size=segment_maker.duration)
        self._attach_left_hand_orientation_notes(nset, segment_maker)
        return nset.novent_line

    def make_musdat(
        self, segment_maker: mus.SegmentMaker, meta_track: mus.MetaTrack
    ) -> old.PolyLine:
        pl = [segment_maker.melodic_orientation]
        dur = segment_maker.duration

        for staff in range(meta_track.n_staves - 1):
            pl.append(lily.NOventLine([lily.NOvent(duration=dur, delay=dur)]))

        pl[-1] = self._make_left_hand(segment_maker)

        return self._prepare_staves(pl, segment_maker)

    def make_sound_engine(self) -> synthesis.SoundEngine:
        return LeftHandKeyboardEngine(
            self._convert_symbolic_novent_line2asterisked_novent_line(self.musdat[2])
        )
