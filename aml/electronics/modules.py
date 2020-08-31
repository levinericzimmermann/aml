"""Blueprint for making live-electronic modules.

Modules can be added to cues.CueOrganiser.
"""

import abc
import pyo


class Module(abc.ABC):
    def __init__(self):
        self._is_playing = False

    @abc.abstractproperty
    def name(self) -> str:
        raise NotImplementedError()

    @abc.abstractproperty
    def mixer(self) -> pyo.Mixer:
        raise NotImplementedError()

    @property
    def isPlaying(self) -> bool:
        return self._is_playing

    def play(self, *args, **kwargs):
        self._is_playing = True
        self._play(*args, **kwargs)

    @abc.abstractmethod
    def _play(self, *args, **kwargs):
        raise NotImplementedError()

    def stop(self):
        self._is_playing = False
        self._stop()

    @abc.abstractmethod
    def _stop(self):
        raise NotImplementedError()
