"""Module for organising cues within a live-electronic framework."""

import pyo

import loclog
import settings


class Cue(object):
    def __init__(self, **module):
        self._module_arguments_pairs = module
        self._parent = None

    def assign_parent(self, parent) -> None:
        self._parent = parent

    def play(self) -> None:
        for module in self._parent.modules:
            try:
                module.play(*self._module_arguments_pairs[module.name])
            except KeyError:
                module.stop()


class CueOrganiser(object):
    def __init__(
        self, modules: tuple,
    ):
        # init private attributes
        self._cues = []
        self._modules = tuple(modules)
        self._current_active_cue = None
        self._current_potential_cue = 0

        # init trigger
        self._new_cue_trigger = pyo.Trig()
        self._stop_cue_trigger = pyo.Trig()
        self._changed_potential_cue_trigger = pyo.Trig()

        # add korg nano control support
        self._add_thresh_button("previous", self.previous_cue)
        self._add_thresh_button("next", self.next_cue)
        self._add_thresh_button("play", self.play)
        self._add_thresh_button("stop", self.stop)

        # init logger
        self._active_module_logger = loclog.ModuleLogger(self)
        self._cue_logger = loclog.CueLogger(self)

    def __len__(self) -> int:
        return len(self._cues)

    def append(self, cue: Cue) -> None:
        assert isinstance(cue, Cue)
        cue.assign_parent(self)
        self._cues.append(cue)

    def extend(self, cues: tuple) -> None:
        [self.append(c) for c in cues]

    def __iter__(self) -> iter:
        return iter(self._cues)

    def __getitem__(self, idx: int) -> Cue:
        return self._cues[idx]

    def _add_thresh_button(
        self, nano_control_button: str, called_method, arg=None
    ) -> None:
        midibutton_name = "_mididata_{}".format(nano_control_button)
        trigger_name = "_trigger_{}".format(nano_control_button)
        trigfunc_name = "_trigfunc_{}".format(nano_control_button)
        chnl, ctrl = settings.KORG_NANOCONTROL2CONTROL_NUMBER[nano_control_button]
        setattr(self, midibutton_name, pyo.Midictl(ctrl, 0, 1, init=0, channel=chnl))
        setattr(self, trigger_name, pyo.Thresh(getattr(self, midibutton_name), 0.95, 0))
        setattr(
            self,
            trigfunc_name,
            pyo.TrigFunc(getattr(self, trigger_name), called_method, arg=arg),
        )

    @property
    def modules(self) -> tuple:
        return self._modules

    @property
    def trigger_play_cue(self) -> pyo.Trig:
        return self._new_cue_trigger

    @property
    def trigger_stop_cue(self) -> pyo.Trig:
        return self._stop_cue_trigger

    @property
    def trigger_choosen_cue(self) -> pyo.Trig:
        return self._changed_potential_cue_trigger

    def next_cue(self) -> None:
        self._changed_potential_cue_trigger.play()
        self._current_potential_cue += 1
        if self._current_potential_cue >= len(self):
            self._current_potential_cue = 0

    def previous_cue(self) -> None:
        self._changed_potential_cue_trigger.play()
        if self._current_potential_cue > 0:
            self._current_potential_cue -= 1
        else:
            self._current_potential_cue = len(self) - 1

    def play(self) -> None:
        self._current_active_cue = self._current_potential_cue
        self[self._current_potential_cue].play()
        self.trigger_play_cue.play(delay=0.05)

    def stop(self):
        [mod.stop() for mod in self.modules]
        self._current_active_cue = None
        self._stop_cue_trigger.play()

    def close(self):
        self.stop()
        self._active_module_logger.close()
        self._cue_logger.close()

    def add_modules_to_mixer(self, mixer: pyo.Mixer) -> None:
        for module in self.modules:
            for (
                physical_output,
                mixer_channel,
            ) in settings.MODULE_MIXER2CHANNEL_MAPPING.items():
                track_mixer_number = (
                    settings.TRACK2MIXER_NUMBER_MAPPING[
                        "{}_{}".format(module.name, physical_output.split("_")[1])
                    ],
                )
                mixer.addInput(
                    track_mixer_number, module.mixer[mixer_channel][0],
                )
                mixer.setAmp(
                    track_mixer_number,
                    settings.PHYSICAL_OUTPUT2CHANNEL_MAPPING[physical_output],
                    1,
                )
