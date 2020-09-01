if __name__ == "__main__":
    import collections
    import functools
    import json
    import operator
    import os

    import pyo

    from mu.mel import ji

    from mu.utils import infit
    from mu.utils import tools

    from mutools import synthesis

    from aml import globals_

    class GenderSampleMaker(synthesis.BasedCsoundEngine):
        gender_samples_path = "aml/electronics/samples/gender/"
        original_gender_samples_path = "{}/original".format(gender_samples_path)
        adapted_gender_samples_path = "{}/adapted".format(gender_samples_path)

        # detect samples with their respective frequencies
        samples = {}
        for sample in os.listdir(original_gender_samples_path):
            if sample[-3:] == "wav":
                sample_name_without_ending = sample[:-4]
                sample_json_name = "{}.json".format(sample_name_without_ending)
                complete_sample_path = "{}/{}".format(
                    original_gender_samples_path, sample
                )
                complete_sample_json_path = "{}/{}".format(
                    original_gender_samples_path, sample_json_name
                )
                frequency = float(
                    tuple(json.load(open(complete_sample_json_path, "r")).values())[0][
                        0
                    ]
                )
                samples.update({frequency: complete_sample_path})

        available_frequencies = tuple(sorted(samples.keys()))

        cname = ".gender_sample_maker"
        tail = 0.25

        freq_used_counter = collections.Counter({freq: 0 for freq in samples})

        sine_attack_maker = infit.Uniform(0.23, 0.58)
        sine_release_maker = infit.Uniform(1.8, 2.2)
        sine_amp_maker = infit.Uniform(0.075, 0.1)

        def __init__(self, index: int, frequency: float):
            closest_frequency = tools.find_closest_item(
                frequency, self.available_frequencies
            )
            second_closest_frequency = tools.find_closest_item(
                frequency,
                tuple(f for f in self.available_frequencies if f != closest_frequency),
            )

            if (
                self.freq_used_counter[closest_frequency]
                <= self.freq_used_counter[second_closest_frequency]
            ):
                choosen_frequency = closest_frequency
            else:
                choosen_frequency = second_closest_frequency

            print(frequency, choosen_frequency)

            self.freq_used_counter.update({choosen_frequency: 1})
            self.choosen_sample = self.samples[choosen_frequency]
            self.pitch_factor = frequency / choosen_frequency
            self.frequency = frequency
            self.duration = pyo.sndinfo(self.choosen_sample)[1] + self.tail
            self.index = index
            self.bandwidth = 2
            self.original_amp = 0.7
            self.bp_amp = 0.0000009
            self.lp_freq = 11000

        @property
        def orc(self) -> str:
            lines = [
                "0dbfs=1",
                "nchnls=2\n",
                "instr 1",
                "kvol0 linseg 0, {}, 1, 0.15, 0.4, {}, 0".format(
                    next(self.sine_attack_maker), next(self.sine_release_maker)
                ),
                "kvol1 linseg 0, {}, 1, 0.15, 0.4, {}, 0".format(
                    next(self.sine_attack_maker), next(self.sine_release_maker)
                ),
                "asine0 poscil3 {} * kvol0, {}".format(
                    next(self.sine_amp_maker), self.frequency * 2
                ),
                "asine1 poscil3 {} * kvol1, {}".format(
                    next(self.sine_amp_maker), self.frequency * 2
                ),
                'asig0, asig1 diskin2 "{}", {}, 0, 0, 0, 4'.format(
                    self.choosen_sample, self.pitch_factor
                ),
                "afilteredsig0 butlp asig0, {}".format(self.lp_freq),
                "afilteredsig1 butlp asig1, {}".format(self.lp_freq),
                "afilteredsig0 buthp afilteredsig0, {}".format(self.frequency * 0.9),
                "afilteredsig1 buthp afilteredsig1, {}".format(self.frequency * 0.9),
                "abp0 reson asig0, {}, {}".format(self.frequency, self.bandwidth),
                "abp1 reson asig1, {}, {}".format(self.frequency, self.bandwidth),
                "outs (afilteredsig0 * {1}) + (abp0 * {0}) + asine0, (afilteredsig1 *"
                " {1}) + (abp1 * {0}) + asine1".format(self.bp_amp, self.original_amp),
                "endin\n",
            ]
            return "\n".join(lines)

        @property
        def sco(self) -> str:
            return "i1 0 {}".format(self.duration)

        def render(self):
            super().render("{}/{}".format(self.adapted_gender_samples_path, self.index))

    # generate adapted sound files
    pitches = sorted(
        functools.reduce(operator.add, globals_.SCALE_PER_INSTRUMENT.values())
    )
    pitches = tuple(
        sorted(
            functools.reduce(
                operator.add,
                tuple(
                    tuple(map(lambda p: p.register(nth), pitches)) for nth in (-1, 0, 1)
                ),
            )
        )
    )
    for idx, pitch in enumerate(pitches):
        freq = float(pitch + ji.r(2, 1)) * globals_.CONCERT_PITCH
        bsm = GenderSampleMaker(idx, freq)
        bsm.render()

    # generate json file for being able to identify pitch
    ji.JIMel(pitches).export2json(
        "aml/electronics/samples/gender/adapted/idx2pitch.json"
    )
