import itertools

import quicktions as fractions

from mu.mel import ji
from mu.utils import infit

from mutools import attachments

from aml import globals_
from aml import tweaks
from aml import versemaker

from aml.trackmaker import keyboard
from aml.trackmaker import strings


def main() -> versemaker.Verse:
    vm = versemaker.VerseMaker(
        59,
        "opening",
        tempo_factor=0.3,
        octave_of_first_pitch=0,
        harmonic_tolerance=0.15,
        ro_temperature=0.67,
        ro_density=0.7,
        harmonic_pitches_tonality_flux_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        harmonic_pitches_complex_interval_helper_maximum_octave_difference_from_melody_pitch=(
            1,
            0,
        ),
        area_density_maker=infit.Gaussian(0.2, 0.01),
        area_density_reference_size=fractions.Fraction(1, 4),
        area_min_split_size=fractions.Fraction(1, 8),
    )

    vm.remove_area(0, 2)
    vm.remove_area(15, 17)
    vm.remove_area(29, len(vm.bars))
    vm.repeat_area(2, 6)

    vm.verse = "opening"

    vm.attach(
        violin=strings.SimpleStringMaker(
            globals_.VIOLIN,
            pizz_maker=infit.ActivityLevel(4, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(5),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(2),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.59,
            harmonic_pitches_density=0.65,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            after_glissando_size=fractions.Fraction(1, 8),
        ),
        viola=strings.SimpleStringMaker(
            globals_.VIOLA,
            tremolo_maker=infit.ActivityLevel(1),
            pizz_maker=infit.ActivityLevel(3, start_at=0),
            acciaccatura_maker=infit.ActivityLevel(7),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(5),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 2, 1, 2, 0, 3)),
            harmonic_pitches_activity=0.56,
            harmonic_pitches_density=0.62,
            shall_add_optional_pitches=True,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_density=0.5,
        ),
        cello=strings.SimpleStringMaker(
            globals_.CELLO,
            tremolo_maker=infit.ActivityLevel(0),
            pizz_maker=infit.ActivityLevel(0),
            force_acciaccatura_to_glissando_maker=infit.ActivityLevel(0),
            acciaccatura_glissando_size_maker=infit.Cycle((0, 1, 0, 1, 2, 0, 1, 0)),
            shall_add_optional_pitches=True,
            acciaccatura_maker=infit.ActivityLevel(9),
            harmonic_pitches_activity=0.57,
            harmonic_pitches_density=0.65,
            optional_pitches_maximum_octave_difference_from_melody_pitch=(1, 0),
            optional_pitches_min_size=fractions.Fraction(1, 8),
            optional_pitches_density=0.6,
        ),
        keyboard=keyboard.KeyboardMaker(),
    )

    #############################################################################
    #                           TWEAKS / post processing                        #
    #############################################################################

    ################################
    #          VIOLIN              #
    ################################

    # tweaks.shorten(2, fractions.Fraction(1, 8), vm.violin.musdat[1])
    tweaks.add_glissando(2, (0, 0, -1), vm.violin.musdat[1], verse_maker=vm)
    tweaks.swap_identity(3, 4, vm.violin.musdat[1])
    # tweaks.split(
    #     8,
    #     fractions.Fraction(1, 4),
    #     fractions.Fraction(1, 8),
    #     fractions.Fraction(1, 8),
    #     vm.violin.musdat[1],
    # )
    tweaks.prolong(5, fractions.Fraction(1, 16), vm.violin.musdat[1])
    tweaks.add_glissando(
        5,
        (-1, 0, 0, -1),
        vm.violin.musdat[1],
        durations=(
            fractions.Fraction(1, 16),
            fractions.Fraction(1, 8),
            fractions.Fraction(1, 8),
        ),
    )
    tweaks.shorten(7, fractions.Fraction(1, 8), vm.violin.musdat[1])
    vm.violin.musdat[1][7].acciaccatura = None
    tweaks.add_glissando(
        7,
        (2, 0, 0, -1),
        vm.violin.musdat[1],
        durations=(
            fractions.Fraction(1, 8),
            fractions.Fraction(1, 8),
            fractions.Fraction(1, 8),
        ),
    )

    tweaks.set_acciaccatura_pitch(11, ji.r(3, 2), vm.violin.musdat[1])

    vm.violin.musdat[1][14].tremolo = None
    vm.violin.musdat[1][14].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    tweaks.rest(4, vm.violin.musdat[1])
    tweaks.prolong(11, fractions.Fraction(1, 4), vm.violin.musdat[1])
    tweaks.split(
        11, vm.violin.musdat[1], fractions.Fraction(1, 4), fractions.Fraction(1, 8)
    )
    tweaks.add_glissando(
        11,
        (0, 0, -1),
        vm.violin.musdat[1],
        durations=(fractions.Fraction(1, 8), fractions.Fraction(1, 8)),
    )
    vm.violin.musdat[1][12].pitch = [ji.r(48, 35)]
    tweaks.rest(18, vm.violin.musdat[1])
    tweaks.change_octave(18, -1, vm.violin.musdat[1], change_main_pitches=False)
    tweaks.split_by_structure(18, 5, vm.violin.musdat[1], vm)
    # tweaks.add_glissando(23, (0, -1), vm.violin.musdat[1], verse_maker=vm)
    tweaks.add_glissando(25, (0, -2), vm.violin.musdat[1], verse_maker=vm)
    tweaks.split_by_structure(30, 2, vm.violin.musdat[1], vm)
    vm.violin.musdat[1][31].acciaccatura = None

    # tweaks.add_artifical_harmonic(
    #     31, vm.violin.musdat[1][31].pitch[0], vm.violin.musdat[1]
    # )
    # vm.violin.musdat[1][31].pitch[0] += ji.r(4, 1)

    ################################
    #          VIOLA               #
    ################################

    tweaks.swap_identity(1, 2, vm.viola.musdat[1])
    vm.viola.musdat[1][2].tremolo = None
    tweaks.rest(3, vm.viola.musdat[1])
    tweaks.prolong(2, fractions.Fraction(1, 16), vm.viola.musdat[1])
    tweaks.rest(6, vm.viola.musdat[1])
    vm.viola.musdat[1][6].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.viola.musdat[1][8].acciaccatura = None
    tweaks.add_glissando(
        8,
        (-2, -2, 0),
        vm.viola.musdat[1],
        durations=(fractions.Fraction(1, 8), fractions.Fraction(1, 16)),
    )
    vm.viola.musdat[1][10].acciaccatura.add_glissando = True
    vm.viola.musdat[1][12].acciaccatura.add_glissando = True

    vm.viola.musdat[1][15].pitch = [ji.r(4, 3)]
    vm.viola.musdat[1][15].volume = 0.5
    vm.viola.musdat[1][15].string_contact_point = attachments.StringContactPoint("arco")

    vm.viola.musdat[1][16].glissando = None
    # tweaks.swap_duration(15, 16, fractions.Fraction(1, 8), vm.viola.musdat[1])
    # tweaks.split(16, fractions.Fraction(1, 8), fractions.Fraction(1, 8), vm.viola.musdat[1])

    tweaks.split_by_structure(18, 2, vm.viola.musdat[1], vm)
    vm.viola.musdat[1][19].acciaccatura = None
    tweaks.add_glissando(19, (0, -1), vm.viola.musdat[1], verse_maker=vm)

    for n in (15, 16, 17, 18, 19, 21):
        tweaks.change_octave(n, -1, vm.viola.musdat[1])

    # tweaks.add_glissando(23, (0, -2), vm.viola.musdat[1], verse_maker=vm)
    tweaks.rest(23, vm.viola.musdat[1])
    vm.viola.musdat[1][25].acciaccatura = None
    vm.viola.musdat[1][25].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.viola.musdat[1][30].acciaccatura = None
    vm.viola.musdat[1][32].string_contact_point = attachments.StringContactPoint("arco")
    vm.viola.musdat[1][32].optional = None
    vm.viola.musdat[1][32].volume = 0.7
    vm.viola.musdat[1][32].pitch[0] -= ji.r(2, 1)
    tweaks.prolong(32, fractions.Fraction(7, 32), vm.viola.musdat[1])

    vm.viola.musdat[1][33].pitch[0] -= ji.r(2, 1)
    vm.viola.musdat[1][33].volume = 0.7

    # tweaks.add_artifical_harmonic(
    #     33, vm.viola.musdat[1][33].pitch[0] - ji.r(2, 1), vm.viola.musdat[1]
    # )
    # vm.viola.musdat[1][33].pitch[0] += ji.r(2, 1)

    ################################
    #          CELLO               # ################################
    vm.cello.musdat[1][1].optional = None
    tweaks.prolong(1, fractions.Fraction(1, 8), vm.cello.musdat[1])
    tweaks.rest(2, vm.cello.musdat[1])
    vm.cello.musdat[1][3].acciaccatura = None
    vm.cello.musdat[1][3].optional = None
    vm.cello.musdat[1][3].pitch[0] += ji.r(2, 1)
    tweaks.rest(5, vm.cello.musdat[1])

    tweaks.prolong(5, fractions.Fraction(1, 8), vm.cello.musdat[1])
    vm.cello.musdat[1][5].optional = None
    vm.cello.musdat[1][5].acciaccatura = None
    vm.cello.musdat[1][5].pitch[0] += ji.r(2, 1)
    tweaks.add_glissando(5, (0, 0, -1), vm.cello.musdat[1], verse_maker=vm)
    vm.cello.musdat[1][7].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    vm.cello.musdat[1][9].string_contact_point = attachments.StringContactPoint(
        "pizzicato"
    )
    tweaks.split_by_structure(9, 3, vm.cello.musdat[1], vm)
    vm.cello.musdat[1][11].bartok_pizzicato = attachments.BartokPizzicato()

    tweaks.rest(13, vm.cello.musdat[1])

    vm.cello.musdat[1][13].acciaccatura = None
    vm.cello.musdat[1][13].pitch = [ji.r(16, 15).register(-1)]
    vm.cello.musdat[1][14].acciaccatura.add_glissando = False

    for n in (13, 14, 15, 16):
        # vm.cello.musdat[1][n].string_contact_point = attachments.StringContactPoint(
        #     "pizzicato"
        # )
        tweaks.change_octave(n, -1, vm.cello.musdat[1])

    for n in (20, 19, 18):
        tweaks.rest(n, vm.cello.musdat[1])

    tweaks.shorten(21, fractions.Fraction(1, 16), vm.cello.musdat[1])

    for n, acc_pitch in zip(
        (18, 19, 21, 23, 24, 25, 26), itertools.cycle((ji.r(7, 8), ji.r(7, 12)))
    ):
        vm.cello.musdat[1][n].string_contact_point = attachments.StringContactPoint(
            "pizzicato"
        )
        if vm.cello.musdat[1][n].acciaccatura:
            if n == 26:
                # tweaks.change_octave(
                #     n, -1, vm.cello.musdat[1], change_main_pitches=False
                # )
                vm.cello.musdat[1][n].acciaccatura = None
            else:
                tweaks.set_acciaccatura_pitch(n, acc_pitch, vm.cello.musdat[1])
                tweaks.change_octave(
                    n, -2, vm.cello.musdat[1], change_acciaccatura_pitches=False
                )

                vm.cello.musdat[1][n].acciaccatura.add_glissando = False

    tweaks.swap_duration(28, 29, fractions.Fraction(1, 16), vm.cello.musdat[1])
    vm.cello.musdat[1][29].acciaccatura = None
    vm.cello.musdat[1][29].optional = None
    tweaks.rest(31, vm.cello.musdat[1])

    for n in (31, 36):
        vm.cello.musdat[1][n].choose = None
        vm.cello.musdat[1][n].pitch = vm.cello.musdat[1][n].pitch[:1]

    vm.cello.musdat[1][33].acciaccatura = None
    vm.cello.musdat[1][34].acciaccatura = None
    vm.cello.musdat[1][38].acciaccatura = None

    tweaks.rest(34, vm.cello.musdat[1])
    tweaks.prolong(33, fractions.Fraction(3, 16), vm.cello.musdat[1])
    tweaks.swap_duration(32, 33, fractions.Fraction(5, 32), vm.cello.musdat[1])
    tweaks.add_glissando(
        32,
        (-1, 0, 0),
        vm.cello.musdat[1],
        durations=(fractions.Fraction(5, 32), fractions.Fraction(5, 16)),
    )

    # CS = fractions.Fraction(7, 4)
    # print(vm.cello.musdat[1].convert2absolute()[18])
    # ev = vm.cello.musdat[1].convert2absolute()[18]
    # for slice_ in vm.bread.find_responsible_slices(CS + ev.delay, CS + ev.duration + 2):
    #     print(slice_.melody_pitch)
    #     print(slice_.harmonic_pitch)
    #     print(slice_.harmonic_field)
    #     print("")

    ################################
    #          keyboard            #
    ################################

    # right hand
    vm.keyboard.musdat[1][13].pitch[0] = vm.keyboard.musdat[1][2].pitch[0].copy()

    # left hand
    vm.keyboard.musdat[2][1].optional = None
    vm.keyboard.musdat[2][20].articulation = attachments.ArticulationOnce(".")
    vm.keyboard.musdat[2][21].arpeggio = None
    vm.keyboard.musdat[2][21].ottava = attachments.Ottava(-1)
    vm.keyboard.musdat[2][21].pitch = list(sorted(vm.keyboard.musdat[2][21].pitch)[:1])
    for n in (35, 34, 33, 32, 28, 27):
        tweaks.rest(n, vm.keyboard.musdat[2])

    tweaks.shorten(40, fractions.Fraction(1, 2), vm.keyboard.musdat[2])

    ################################
    #  changes for all instrument  #
    ################################

    for instr in ("violin", "viola", "cello", "keyboard"):
        if instr == "keyboard":
            nth_line = 2
        else:
            nth_line = 1

        getattr(vm, instr)[nth_line][0].dynamic = attachments.Dynamic("pp")

    verse = vm()
    return verse
