"""String - processing and spatialisation module."""

import pyo

import modules


class String(object):
    def __init__(self, signal: pyo.Input) -> None:
        self.signal = signal
        self.follower = pyo.Follower(self.signal, freq=30)
        self.attack_detector = pyo.AttackDetector(
            self.signal,
            deltime=0.005,
            cutoff=10,
            maxthresh=3,
            minthresh=-30,
            reltime=0.1,
        )
        self.pitch_tracker = pyo.Yin(
            self.signal,
            tolerance=0.2,
            minfreq=40,
            maxfreq=1000,
            cutoff=1000,
            winsize=1024,
            mul=1,
            add=0,
        )
        self.pitch_tracker.stop()
        self.attack_detector.stop()
        self.processed_signal = signal


class StringProcesser(modules.Module):
    """Live-Electronic module for processing strings."""

    name = 'strings'

    def __init__(self, strings: dict, midi_synth: object):
        super().__init__()

        self.strings = strings
        self.midi_synth = midi_synth
        self._mixer = pyo.Mixer(outs=4, chnls=1, time=0.025)

        self.instrument2channel_mapping = {
            instrument: (tuple(range(n, n + 4)), tuple(range(4)))
            for instrument, n in zip(self.strings, range(0, 4 * len(self.strings), 4))
        }

        for instrument_name, instrument_object in self.strings.items():
            for input_chnl, output_chnl in zip(
                *self.instrument2channel_mapping[instrument_name]
            ):
                self.mixer.addInput(
                    input_chnl, instrument_object.processed_signal
                )
                self.mixer.setAmp(input_chnl, output_chnl, 0)

    @property
    def mixer(self) -> pyo.Mixer:
        return self._mixer

    def _play(self, *args, **kwargs):
        pass

    def _stop(self):
        pass
