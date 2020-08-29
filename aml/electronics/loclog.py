"""Module for logging crucial information to the user."""

import operator
import os

import pyo

import settings
import subprocess
import utility


class TermLogger(object):
    def close(self):
        self._process.terminate()
        cmd = "TERMPID=$(ps -ef | grep xterm | grep {} ".format(self._title)
        cmd += r"| head -1 | awk '{ print $2 }'); kill $TERMPID"
        subprocess.call(
            [cmd], shell=True,
        )


class LogTermLogger(TermLogger):
    def close(self):
        super().close()
        os.remove(self._path)


class Meter(LogTermLogger):
    _n_bars = 55
    _min = 0
    _max = 0.4

    def __init__(self, *name_signal_pair, title: str = "INPUTS"):
        self._title = title
        self._n_signals = len(name_signal_pair)
        self._names = tuple(map(operator.itemgetter(0), name_signal_pair))
        self._signals = tuple(map(operator.itemgetter(1), name_signal_pair))
        self._n_channel_signals = []
        for idx, signal in enumerate(self._signals):
            mixed_sig = signal.mix(self._n_signals) * [
                1 if subidx == idx else 0 for subidx in range(self._n_signals)
            ]
            self._n_channel_signals.append(mixed_sig)

        self._tracker = pyo.RMS(sum(self._n_channel_signals), self._track)
        self._path = "LOG_INPUT"

        with open(self._path, "w") as f:
            f.write("")

        self._process = utility.logfile(
            self._path,
            x=70,
            y=1 + len(name_signal_pair),
            xoff="-0",
            yoff="+0",
            title=self._title,
        )

        longest_name_size = max(tuple(map(len, self._names)))
        self._title_per_signal = []
        for name in self._names:
            diff = longest_name_size - len(name)
            self._title_per_signal.append("RMS-{}{}: ".format(name, " " * diff))

    @property
    def name(self) -> str:
        return self._name

    def _make_bar(self, value: float) -> str:
        value = min((value, self._max))
        percentage = value / self._max
        bars = int(self._n_bars * percentage)
        return "".join((["#"] * bars) + ([" "] * (self._n_bars - bars)))

    def _track(self, *args) -> None:
        with open(self._path, "w") as f:
            data = []
            data.extend(
                [
                    "{}{}".format(title, self._make_bar(value))
                    for title, value in zip(self._title_per_signal, args)
                ]
            )
            f.write("\n".join(data) + "\n")


class MidiDataLogger(LogTermLogger):
    def __init__(self):
        self._path = settings.MIDI_CONTROL_LOGGING_FILE
        self._last_ctl_data = (None, None)
        self._last_note_data = (None, None, None)
        self._last_note_off_data = (None, None)
        self._title = "MIDI-DATA-LOGGING"
        self._rewrite()

        self._process = utility.logfile(
            self._path, x=80, y=4, xoff="+0", yoff="-430", title=self._title,
        )

        # Function called by CtlScan2 object.
        def scanner(ctlnum, midichnl):
            self._last_ctl_data = (midichnl, ctlnum)
            self._rewrite()

        # Listen to controller input.
        self._scan = pyo.CtlScan2(scanner, toprint=False)

    def _rewrite(self) -> None:
        with open(settings.MIDI_CONTROL_LOGGING_FILE, "w") as f:
            data = [
                "CTRL-MSG:   --- channel: '{}', control number: '{}'".format(
                    *self._last_ctl_data
                ),
                "NOTE-ON-MSG --- voice: '{}', midi-pitch'{}', velocity: '{}'".format(
                    *self._last_note_data
                ),
                "NOTE-OFF-MSG --- voice: '{}', midi-pitch'{}'".format(
                    *self._last_note_off_data
                ),
            ]
            f.write("\n".join(data) + "\n")

    def load_note_on_data(self, voice: int, midi_note: int, velocity: float) -> None:
        self._last_note_data = (voice, midi_note, velocity)
        self._rewrite()

    def load_note_off_data(self, voice: int, midi_note: int) -> None:
        self._last_note_off_data = (voice, midi_note)
        self._rewrite()


class HtopLogger(TermLogger):
    def __init__(self):
        self._title = "HTOP"
        self._process = utility.load_terminal(
            "htop", x=70, y=19, xoff="-0", yoff="-0", title="HTOP"
        )
