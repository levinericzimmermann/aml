import pyo

import settings


class MixHelper(object):
    min_vol_scale = 0
    max_vol_scale = 2

    def __init__(
        self, mixer: pyo.Mixer, name: str, scene_number: int, strip_number: int
    ):
        self.name = name
        self.mixer = mixer
        vc_channel, vc_ctl_number = settings.KORG_NANOCONTROL2CONTROL_NUMBER[
            "slider{}{}".format(scene_number, strip_number)
        ]
        volume_controller = pyo.Midictl(
            vc_ctl_number,
            self.min_vol_scale,
            self.max_vol_scale,
            init=0.5,
            channel=vc_channel,
        )
        portamento = pyo.Port(volume_controller, risetime=0.075, falltime=0.0075)
        self.mixer.mul = portamento
        # self.mixer.ctrl(title=name, map_list=[pyo.SLMapMul(init=1)])


class MixSystem(object):
    def __init__(self, **name_mixer_pair):
        self.mix_helpers = tuple(
            MixHelper(
                mixer,
                name,
                settings.CONTROLLED_SIGNAL_SCENE,
                settings.CONTROLLED_SIGNAL2KORG_NANOCONTROL_STRIP[name],
            )
            for name, mixer in name_mixer_pair.items()
        
        )
        # TODO(add Mute/Solo-button functionality)
