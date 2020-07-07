# main program for raspberry pi / keyboard!
# shall start automatically after computer got booted

# (0) preparing computer for performance

# turn off any networking
# nmcli networking off

# turn off bluetooth
rfkill block bluetooth

# (1) starting audio engine

# starting qjack first and exiting again because otherwise jack_control
# won't be able to start dbus for some unknown reasons.
# qjackctl -s &
# sleep 1
# kill $!

# starting jack
jack_control start
jack_control ds alsa
jack_control dps device hw:K6  # change according to used USB-audio interface
jack_control dps rate 44100
jack_control dps period 512
jack_control dps outchannels 4

sleep 5

qjackctl -a patchbay.xml &
QJACKCTL_PID=$!

# (2) starting actual sound generation programs (pianoteq and pyo)

pianoteq --headless --preset "Concert Harp Daily" --fxp aml.fxp --midimapping complete --multicore max &
PIANOTEQ_PID=$!
# waiting for pianoteq to boot
sleep 2
# running pyo script
python3 main.py

# (3) ending program

sleep 0.5
# killing pianoteq process when stopping pyo script
kill $PIANOTEQ_PID
kill $QJACKCTL_PID

jack_control exit

# shutting down computer
shutdown 0
