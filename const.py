from typing import Dict
from homeassistant.const import Platform
from homeassistant.components.media_player import MediaPlayerState, RepeatMode

from linkplay.consts import PlayingStatus, PlaymodeSupport, LoopMode, EqualizerMode

DOMAIN = "linkplay"
CONF_IP = "ip"
PLATFORMS = [Platform.MEDIA_PLAYER]

STATE_MAP: Dict[PlayingStatus, MediaPlayerState] = {
    PlayingStatus.STOPPED:  MediaPlayerState.IDLE,
    PlayingStatus.PAUSED:   MediaPlayerState.PAUSED,
    PlayingStatus.PLAYING:  MediaPlayerState.PLAYING,
    PlayingStatus.LOADING:  MediaPlayerState.BUFFERING
}

INPUT_MAP: Dict[PlaymodeSupport, str] = {
    PlaymodeSupport.LINE_IN: "Line In",
    PlaymodeSupport.BLUETOOTH: "Bluetooth",
    PlaymodeSupport.USB: "USB",
    PlaymodeSupport.OPTICAL: "Optical",
    PlaymodeSupport.COAXIAL: "Coaxial",
    PlaymodeSupport.LINE_IN_2: "Line In 2",
    PlaymodeSupport.USBDAC: "USB DAC",
    PlaymodeSupport.OPTICAL_2: "Optical 2"
}

SOURCE_MAP: Dict[str, PlaymodeSupport] = {v: k for k, v in INPUT_MAP.items()}

REPEAT_MAP: Dict[LoopMode, RepeatMode] = {
    LoopMode.CONTINOUS_PLAY_ONE_SONG: RepeatMode.ONE,
    LoopMode.PLAY_IN_ORDER: RepeatMode.OFF,
    LoopMode.CONTINUOUS_PLAYBACK: RepeatMode.ALL,
    LoopMode.RANDOM_PLAYBACK: RepeatMode.ALL,
    LoopMode.LIST_CYCLE: RepeatMode.ALL
}

SOUND_MAP: Dict[EqualizerMode, str] = {
    EqualizerMode.NONE: "None",
    EqualizerMode.CLASSIC: "Classic",
    EqualizerMode.POP: "Pop",
    EqualizerMode.JAZZ: "Jazz",
    EqualizerMode.VOCAL: "Vocal"
}

EQUALIZER_MAP: Dict[str, EqualizerMode] = {v: k for k, v in SOUND_MAP.items()}
SOUND_LIST: list[str] = list(SOUND_MAP.values())