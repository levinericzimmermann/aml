from aml import globals_

from . import scales
from . import twelfth_tone_accidentals


TWELFTH_TONE_EXPLANATION_PATH = "{}/twelfth_tone_explanation".format(
    globals_.INTRODUCTION_PICTURES_PATH
)

twelfth_tone_accidentals.main(TWELFTH_TONE_EXPLANATION_PATH)
scales.main(globals_.INTRODUCTION_PATH)
