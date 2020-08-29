"""Simple pyo script for testing & balancing speaker."""


if __name__ == "__main__":
    import argparse
    import itertools
    import subprocess
    import time

    import pyo

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--channels", type=int, default=2)
    PARSER.add_argument("--increment", type=int, default=0)
    PARSER.add_argument("--mul", type=float, default=0.35)
    PARSER.add_argument("--time", type=float, default=1)
    PARSER.add_argument("--type", type=str, default="noise")

    PARSED_ARGS = PARSER.parse_args()
    N_CHANNELS = PARSED_ARGS.channels
    MUL = PARSED_ARGS.mul
    TIME = PARSED_ARGS.time
    INCREMENT = PARSED_ARGS.increment
    TYPE = PARSED_ARGS.type.lower()

    # start performance mode
    subprocess.run("performance_on.sh", shell=True, stdout=subprocess.DEVNULL)

    # start jack
    subprocess.run("qjackctl -s &", shell=True, stdout=subprocess.DEVNULL)
    time.sleep(0.5)

    SERVER = pyo.Server(audio="jack", midi="jack", nchnls=N_CHANNELS,)

    # starting server
    SERVER.boot()

    # starting sound loop
    _speaker_cycle = itertools.cycle(range(INCREMENT, N_CHANNELS + INCREMENT))

    ALLOWED_TYPES = {"noise": pyo.Noise(), "sine": pyo.Sine(freq=400)}
    try:
        SIGNAL = ALLOWED_TYPES[TYPE]
    except KeyError:
        msg = "Unknown type '{}'. Valid types would be '{}'.".format(
            TYPE, ALLOWED_TYPES
        )
        raise NotImplementedError(msg)

    FADER = pyo.Fader(fadein=0.07, fadeout=0.07, dur=TIME, mul=MUL)
    SIGNAL.mul = FADER

    # red & bold printing
    print(
        "\033[91m", "\033[1m", "\n",
    )

    def _loop() -> None:
        speaker = next(_speaker_cycle)
        print(
            "SPEAKER: ", "{}".format(speaker + 1), sep="", end="\r", flush=True,
        )
        SIGNAL.out(speaker, dur=TIME)
        FADER.play(dur=TIME)

    LOOP = pyo.Pattern(_loop, TIME + 0.075)
    LOOP.play()

    # starting server & gui
    SERVER.start()
    SERVER.gui(locals(), title="test-speaker", exit=False)

    # -----exiting
    subprocess.run("performance_off.sh", shell=True, stdout=subprocess.DEVNULL)
