"""Module for different classes that are able to manage the spatialisation of signals."""

import abc
import collections

import pyo


class _Spat(pyo.Mix):
    def __init__(self, signal: pyo.PyoObject, n_voices: int):
        self._control_signals = [pyo.Sig(0) for _ in range(n_voices)]
        super().__init__(signal, voices=n_voices, mul=self.control_signals)

    @property
    def control_signals(self) -> list:
        return self._control_signals


class SpatMaker(abc.ABC):
    @abc.abstractproperty
    def spat_class(self) -> type(_Spat):
        raise NotImplementedError

    def make_spatialised_signal(
        self, signal: pyo.PyoObject, n_voices: int, *args, **kwargs
    ) -> _Spat:
        return self.spat_class(signal, n_voices, *args, **kwargs)


################################################################
# spat module that always tries to set amp parameters so that  #
# the differences in rms between individual channels is as low #
# as possible (when updating the Spat - object).               #
################################################################


class _BalancedSpat(_Spat):
    def update(self) -> None:
        avg_rms_per_channel = self._parent.get_avg_rms_per_channel()
        minima = min(avg_rms_per_channel)
        choosen_channel = avg_rms_per_channel.index(minima)
        for idx, signal in enumerate(self.control_signals):
            signal.value = int(idx == choosen_channel)  # 1 for lowest channel, 0 for all other


class BalancedSpatMaker(SpatMaker):
    spat_class = _BalancedSpat

    def __init__(self, signal_per_channel: list, n_stored_rms_values: int = 15):
        self._signal_per_channel = signal_per_channel
        self._rms_per_channel = [
            collections.deque([], maxlen=n_stored_rms_values)
            for _ in signal_per_channel
        ]
        self._rms_tracker = pyo.RMS(
            self._signal_per_channel,
            function=lambda *values: [
                self._rms_per_channel[nth].append(value)
                for nth, value in enumerate(values)
            ],
        )

    def get_avg_rms_per_channel(self) -> tuple:
        return tuple(sum(last_rms_values) for last_rms_values in self._rms_per_channel)

    def make_spatialised_signal(
        self, signal: pyo.PyoObject, n_voices: int, *args, **kwargs
    ) -> _BalancedSpat:
        spat = super().make_spatialised_signal(signal, n_voices, *args, **kwargs)
        spat._parent = self
        return spat
