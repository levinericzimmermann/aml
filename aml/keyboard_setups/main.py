import pyo
import right_hand_synth

if __name__ == "__main__":
    s = pyo.Server(audio="jack", midi="jack")

    # listening / sending to all midi output devices
    s.setMidiInputDevice(99)
    s.setMidiOutputDevice(99)

    # starting server
    s.boot()
    s.start()

    # generating objects
    rhs = right_hand_synth.RightHandSynth()
    rhs.notes.keyboard()

    # starting gui
    s.gui(locals())
