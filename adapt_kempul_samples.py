if __name__ == "__main__":
    import collections
    import os
    import json

    import pyo

    from mu.utils import tools

    from mutools import synthesis

    from aml import globals_
    from aml.trackmaker import keyboard

    class KempulSampleMaker(synthesis.BasedCsoundEngine):
        kempul_samples_path = "aml/keyboard_setups/kempul_samples"
        original_kempul_samples_path = "{}/original".format(kempul_samples_path)
        adapted_kempul_samples_path = "{}/adapted".format(kempul_samples_path)

        # detect samples with their respective frequencies
        samples = {}
        for sample in os.listdir(original_kempul_samples_path):
            if sample[-3:] == "wav":
                sample_name_without_ending = sample[:-4]
                sample_json_name = "{}.json".format(sample_name_without_ending)
                complete_sample_path = "{}/{}".format(
                    original_kempul_samples_path, sample
                )
                complete_sample_json_path = "{}/{}".format(
                    original_kempul_samples_path, sample_json_name
                )
                frequency = float(
                    tuple(json.load(open(complete_sample_json_path, "r")).values())[0][
                        0
                    ]
                )
                samples.update({frequency: complete_sample_path})

        available_frequencies = tuple(sorted(samples.keys()))

        cname = ".kempul_sample_maker"
        tail = 4

        freq_used_counter = collections.Counter({freq: 0 for freq in samples})

        def __init__(self, index: int, frequency: float):
            closest_frequency = tools.find_closest_item(
                freq, self.available_frequencies
            )
            second_closest_frequency = tools.find_closest_item(
                freq,
                tuple(f for f in self.available_frequencies if f != closest_frequency),
            )

            if (
                self.freq_used_counter[closest_frequency]
                <= self.freq_used_counter[second_closest_frequency]
            ):
                choosen_frequency = closest_frequency
            else:
                choosen_frequency = second_closest_frequency

            self.freq_used_counter.update({choosen_frequency: 1})

            self.choosen_sample = self.samples[choosen_frequency]
            self.pitch_factor = frequency / choosen_frequency
            self.frequency = frequency
            self.duration = pyo.sndinfo(self.choosen_sample)[1] + self.tail
            self.index = index

        @property
        def orc(self) -> str:
            lines = [
                "0dbfs=1",
                "nchnls=2\n",
                "instr 1",
                "kvol linseg 0, 0.3, 1, 0.2, 0.5, 3.4, 0",
                "asine poscil3 0.385 * kvol, {}".format(self.frequency),
                'asig0, asig1 diskin2 "{}", {}, 0, 0, 6, 4'.format(
                    self.choosen_sample, self.pitch_factor
                ),
                "outs asig0 + asine, asig1 + asine",
                "endin\n",
            ]
            return "\n".join(lines)

        @property
        def sco(self) -> str:
            return "i1 0 {}".format(self.duration)

        def render(self):
            super().render("{}/{}".format(self.adapted_kempul_samples_path, self.index))

    # generate adapted sound files
    pitches = sorted(keyboard.MIDI_NOTE2JI_PITCH_PER_ZONE["gong"].values())
    for idx, pitch in enumerate(pitches):
        freq = float(pitch) * globals_.CONCERT_PITCH
        ksm = KempulSampleMaker(idx, freq)
        ksm.render()
