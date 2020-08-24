import os

import pyo

import utility


class Meter(object):
    _n_bars = 55
    _min = 0
    _max = 0.5

    def __init__(self, name: str, signal: pyo.Input):
        self._name = name
        self._signal = signal
        self._tracker = pyo.RMS(self._signal, self._track)
        self._logfile_name = "LOG_{}".format(self._name)

        with open(self._logfile_name, "w") as f:
            f.write('')

        self._meter_process = utility.logfile(
            self._logfile_name, x=70, y=1, xoff=100, yoff=0
        )
        self._last_value = 0.3

    @property
    def name(self) -> str:
        return self._name

    def _track(self, *args) -> None:
        value = round(args[0], 4)
        if value != self._last_value:
            value = min((value, self._max))
            percentage = value / self._max
            bars = int(self._n_bars * percentage)
            with open(self._logfile_name, "w") as f:
                # f.write('{}\r'.format(value))
                f.write(
                    "RMS-{}: {}\r".format(
                        self._name,
                        "".join((["#"] * bars) + ([" "] * (self._n_bars - bars))),
                    )
                )
            self._last_value = value

    def close(self):
        self._meter_process.terminate()
        os.remove(self._logfile_name)
