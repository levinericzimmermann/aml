""""""

import pyo


class String(object):
    def __init__(self, signal: pyo.Input) -> None:
        self.signal = signal
        # self.follower = pyo.Follower(self.signal, freq=30)
        # self.attack_detector = pyo.AttackDetector(
        #     self.signal,
        #     deltime=0.005,
        #     cutoff=10,
        #     maxthresh=3,
        #     minthresh=-30,
        #     reltime=0.1,
        # )
        # self.pitch_tracker = pyo.Yin(
        #     self.signal,
        #     tolerance=0.2,
        #     minfreq=40,
        #     maxfreq=1000,
        #     cutoff=1000,
        #     winsize=1024,
        #     mul=1,
        #     add=0,
        # )
        self.processed_signal = signal


class StringProcesser(object):
    def __init__(self, strings: dict, midi_synth: object):
        self.strings = strings
        self.midi_synth = midi_synth
        self.strings_mixer = pyo.Mixer(outs=4, chnls=1, time=0.025)

        self.instrument2channel_mapping = {
            instrument: (tuple(range(n, n + 4)), tuple(range(4)))
            for instrument, n in zip(self.strings, range(0, 4 * len(self.strings), 4))
        }

        for instrument_name, instrument_object in self.strings.items():
            for input_chnl, output_chnl in zip(
                *self.instrument2channel_mapping[instrument_name]
            ):
                self.strings_mixer.addInput(
                    input_chnl, instrument_object.processed_signal
                )
                self.strings_mixer.setAmp(input_chnl, output_chnl, 0)
