performance_on.sh

qjackctl -a patchbay.xml -s & QJACKCTL_PID=$!

# waiting for jack to boot
sleep 1

# (1) starting actual sound generation programs (pianoteq and pyo)

pianoteq --headless --preset "Concert Harp Daily" --fxp aml.fxp --midimapping complete --multicore max &
PIANOTEQ_PID=$!
# waiting for pianoteq to boot
sleep 2

# running pyo script
python3 main.py

# (2) ending program

sleep 0.5

# killing pianoteq & qjackctl process when stopping pyo script
kill $PIANOTEQ_PID
kill $QJACKCTL_PID

performance_off.sh
