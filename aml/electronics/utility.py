import subprocess

import settings


def load_terminal(
    command: str, x: int = 20, y: int = 30, xoff='+0', yoff='+0', title: str = "",
) -> subprocess.Popen:
    x *= settings.TERMINAL_LOGGING_SCALING
    y *= settings.TERMINAL_LOGGING_SCALING
    xoff *= settings.TERMINAL_LOGGING_SCALING
    yoff *= settings.TERMINAL_LOGGING_SCALING
    return subprocess.Popen(
        [
            "xterm -title {} -fa monaco -fs 13 -geometry {}x{}{}{} -e {}".format(
                title, x, y, xoff, yoff, command
            )
        ],
        shell=True,
    )


def logfile(
    path: str, x: int = 20, y: int = 30, xoff='+0', yoff='+0', title: str = ""
) -> subprocess.Popen:
    return load_terminal(
        "tail -f {} 2> /dev/null".format(path), x, y, xoff, yoff, title
    )
