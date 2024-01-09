from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.util.dt import utcnow

from linkplay.discovery import linkplay_factory_bridge
from linkplay.bridge import LinkPlayBridge
from linkplay.consts import LoopMode, PlayingStatus

from .const import (
    DOMAIN,
    CONF_IP,
    STATE_MAP,
    INPUT_MAP,
    SOURCE_MAP,
    REPEAT_MAP,
    MediaPlayerState,
    SOUND_MAP,
    SOUND_LIST
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

        self._attr_sound_mode_list = SOUND_LIST
        self._attr_should_poll = True
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PAUSE,
            MediaPlayerEntityFeature.PLAY,
            MediaPlayerEntityFeature.PLAY_MEDIA,
            MediaPlayerEntityFeature.PREVIOUS_TRACK,
            MediaPlayerEntityFeature.NEXT_TRACK,
            MediaPlayerEntityFeature.REPEAT_SET,
            MediaPlayerEntityFeature.STOP,
            MediaPlayerEntityFeature.VOLUME_MUTE,
            MediaPlayerEntityFeature.VOLUME_SET,
            MediaPlayerEntityFeature.SELECT_SOURCE,
            MediaPlayerEntityFeature.SELECT_SOUND_MODE
        )

    async def async_update(self):
        """Update the state of the media player."""

        try:
            await self.bridge.device.update_status()
        except:
            self._attr_available = False
            self._attr_state = MediaPlayerState.OFF
            return

        self._attr_available = True
        self._attr_unique_id = f"{DOMAIN}.media_player.{self.bridge.device.uuid}"
        self.entity_id = self._attr_unique_id
        self._attr_state = STATE_MAP[self.bridge.player.status]
        self._attr_volume_level = self.bridge.player.volume / 100
        self._attr_name = self.bridge.device.name
        self._attr_is_volume_muted = self.bridge.player.muted or self.bridge.player.volume == 0

        self._attr_source_list = []
        for playmode in self.bridge.device.playmode_support:
            self._attr_source_list.append(INPUT_MAP[playmode])

        self._attr_source = SOURCE_MAP[self.bridge.player.playback_mode]
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
            #self._attr_media_content_type

        else:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
            self._attr_media_artist = None
            self._attr_media_title = None
            self._attr_media_album_name = None
            self._attr_media_content_type = None


