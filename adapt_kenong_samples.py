if __name__ == "__main__":
    import collections
    import json
    import os

    import pyo

    from mu.mel import ji
    from mu.utils import tools

    from mutools import synthesis

    from aml import globals_
    from aml.trackmaker import keyboard

    class KenongSampleMaker(synthesis.BasedCsoundEngine):
        kenong_samples_path = "aml/electronics/kenong_samples"
        original_kenong_samples_path = "{}/original".format(kenong_samples_path)
        adapted_kenong_samples_path = "{}/adapted".format(kenong_samples_path)

        # detect samples with their respective frequencies
        samples = {}
        for sample in os.listdir(original_kenong_samples_path):
            if sample[-3:] == "wav":
                sample_name_without_ending = sample[:-4]
                sample_json_name = "{}.json".format(sample_name_without_ending)
                complete_sample_path = "{}/{}".format(
                    original_kenong_samples_path, sample
                )
                complete_sample_json_path = "{}/{}".format(
                    original_kenong_samples_path, sample_json_name
                )
                frequency = float(
                    tuple(json.load(open(complete_sample_json_path, "r")).values())[0][
                        0
                    ]
                )
                samples.update({frequency: complete_sample_path})

        available_frequencies = tuple(sorted(samples.keys()))

        cname = ".kenong_sample_maker"
        tail = 4

        freq_used_counter = collections.Counter({freq: 0 for freq in samples})

        def __init__(self, index: int, frequency: float):
            if frequency < 300:
                frequency *= 2
            closest_frequency = tools.find_closest_item(
                frequency, self.available_frequencies
            )
            print(frequency, closest_frequency)
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

            self.freq_used_counter.update({choosen_frequency: 1})

            self.choosen_sample = self.samples[choosen_frequency]
            self.pitch_factor = frequency / choosen_frequency
            print(self.pitch_factor)
            self.frequency = frequency
            self.duration = pyo.sndinfo(self.choosen_sample)[1] + self.tail
            self.index = index

        @property
        def orc(self) -> str:
            lines = [
                "0dbfs=1",
                "nchnls=2\n",
                "instr 1",
                "kvol linseg 0, 0.2, 1, 0.15, 0.5, 3, 0",
                "asine poscil3 0.35 * kvol, {}".format(self.frequency),
                'asig0, asig1 diskin2 "{}", {}, 0, 0, 0, 4'.format(
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
            super().render("{}/{}".format(self.adapted_kenong_samples_path, self.index))

    # generate adapted sound files
    pitches = sorted(keyboard.MIDI_NOTE2JI_PITCH_PER_ZONE["gong"].values())
    for idx, pitch in enumerate(pitches):
        freq = float(pitch + ji.r(2, 1)) * globals_.CONCERT_PITCH
        ksm = KenongSampleMaker(idx, freq)
        ksm.render()
