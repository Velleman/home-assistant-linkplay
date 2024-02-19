from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerDeviceClass, MediaType
from homeassistant.util.dt import utcnow

from linkplay.discovery import linkplay_factory_bridge
from linkplay.bridge import LinkPlayBridge
from linkplay.consts import LoopMode, PlayingStatus, PlaybackMode

from .const import (
    DOMAIN,
    CONF_IP,
    STATE_MAP,
    INPUT_MAP,
    SOURCE_MAP,
    REPEAT_MAP,
    MediaPlayerState,
    SOUND_MAP,
    SOUND_LIST,
    EQUALIZER_MAP
)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a media player from a config entry."""

    session = async_get_clientsession(hass)

    @callback
    async def async_create_entity() -> None:
        bridge = await linkplay_factory_bridge(entry.data[CONF_IP], session)
        if bridge:
            hass.data[DOMAIN][entry.entry_id] = bridge
            async_add_entities([LinkPlayMediaPlayerEntity(bridge)])
 

    await async_create_entity()


class LinkPlayMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a LinkPlay media player."""
    bridge: LinkPlayBridge
   
    def __init__(self, bridge: LinkPlayBridge):
        self.bridge = bridge

        self._attr_unique_id = f"{DOMAIN}.{self.bridge.device.uuid}"
        self.entity_id = self._attr_unique_id
        self._attr_name = self.bridge.device.name
        self._attr_sound_mode_list = SOUND_LIST
        self._attr_should_poll = True
        self._attr_device_class = MediaPlayerDeviceClass.RECEIVER
        #self._attr_source_list = [INPUT_MAP[playmode] for playmode in self.bridge.device.playmode_support]
        self._attr_source_list = ["wifi", "line-in"]
        self._attr_media_content_type = MediaType.MUSIC
        self._attr_supported_features = MediaPlayerEntityFeature.PAUSE | \
            MediaPlayerEntityFeature.PLAY | \
            MediaPlayerEntityFeature.PLAY_MEDIA | \
            MediaPlayerEntityFeature.PREVIOUS_TRACK | \
            MediaPlayerEntityFeature.NEXT_TRACK | \
            MediaPlayerEntityFeature.REPEAT_SET | \
            MediaPlayerEntityFeature.STOP | \
            MediaPlayerEntityFeature.VOLUME_MUTE | \
            MediaPlayerEntityFeature.VOLUME_SET | \
            MediaPlayerEntityFeature.SELECT_SOURCE | \
            MediaPlayerEntityFeature.SELECT_SOUND_MODE | \
            MediaPlayerEntityFeature.SEEK

    async def async_update(self):
        """Update the state of the media player."""

        try:
            await self.bridge.player.update_status()
        except:
            self._attr_available = False
            self._attr_state = MediaPlayerState.OFF
            return

        self._attr_available = True
        self._attr_state = STATE_MAP[self.bridge.player.status]
        self._attr_volume_level = self.bridge.player.volume / 100
        self._attr_is_volume_muted = self.bridge.player.muted
        self._attr_source = "wifi"#SOURCE_MAP[self.bridge.player.playback_mode]
        self._attr_repeat = REPEAT_MAP[self.bridge.player.loop_mode]
        self._attr_shuffle = self.bridge.player.loop_mode == LoopMode.RANDOM_PLAYBACK
        self._attr_sound_mode = SOUND_MAP[self.bridge.player.equalizer_mode]

        if self.bridge.player.status == PlayingStatus.PLAYING:
            self._attr_media_position = self.bridge.player.current_position / 1000
            self._attr_media_position_updated_at = utcnow()
            self._attr_media_duration = self.bridge.player.total_length / 1000
            self._attr_media_artist = self.bridge.player.artist
            self._attr_media_title = self.bridge.player.title
            self._attr_media_album_name = self.bridge.player.album

        else:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
            self._attr_media_artist = None
            self._attr_media_title = None
            self._attr_media_album_name = None
            self._attr_media_content_type = None

    async def async_select_source(self, source: str) -> None:
        await self.bridge.player.set_play_mode(PlaybackMode.LINE_IN)

    async def async_select_sound_mode(self, sound_mode: str):
        """Switch the sound mode of the entity."""
        await self.bridge.player.set_equalizer_mode(EQUALIZER_MAP[sound_mode])

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        if mute:
            await self.bridge.player.mute()
        else:
            await self.bridge.player.unmute()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self.bridge.player.set_volume(int(volume * 100))

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.bridge.player.pause()

    async def async_media_play(self) -> None:
        """Send play command."""
        if self.bridge.player.status == PlayingStatus.PAUSED:
            await self.bridge.player.resume()
