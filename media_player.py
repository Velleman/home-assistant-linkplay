from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.components import media_source
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
    MediaType,
    RepeatMode,
    BrowseMedia
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow

from linkplay.bridge import LinkPlayBridge, LinkPlayMultiroom
from linkplay.consts import LoopMode, PlayingStatus
from linkplay.controller import LinkPlayController

from .const import (
    DOMAIN,
    BRIDGE_DISCOVERED,
    CONTROLLER,
    STATE_MAP,
    REPEAT_MAP,
    REPEAT_MAP_INV,
    EQUALIZER_MAP,
    EQUALIZER_MAP_INV,
    SOURCE_MAP,
    SOURCE_MAP_INV,
    DEFAULT_FEATURES,
    SEEKABLE_FEATURES
)
from .model_registry import get_info_from_project
from .utils import get_active_multiroom

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up a media player from a config entry."""

    @callback
    def add_entity(bridge: LinkPlayBridge):
        async_add_entities([LinkPlayMediaPlayerEntity(bridge)])

    entry.async_on_unload(
        async_dispatcher_connect(hass, BRIDGE_DISCOVERED, add_entity)
    )

class LinkPlayMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a LinkPlay media player."""

    def __init__(self, bridge: LinkPlayBridge):
        self.bridge = bridge

        self._attr_unique_id = self.entity_id = f"{DOMAIN}.{self.bridge.device.uuid}"
        self._attr_name = self.bridge.device.name
        self._attr_sound_mode_list = list(EQUALIZER_MAP.values())
        self._attr_should_poll = True
        self._attr_device_class = MediaPlayerDeviceClass.RECEIVER
        self._attr_source_list = [SOURCE_MAP[playing_mode] for playing_mode in self.bridge.device.playmode_support]
        self._attr_media_content_type = MediaType.MUSIC

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return the device info."""
        manufacturer, model = get_info_from_project(self.bridge.device.properties["project"])
        return dr.DeviceInfo(
            configuration_url=self.bridge.endpoint,
            connections={(dr.CONNECTION_NETWORK_MAC, self.bridge.device.properties["MAC"])},
            entry_type=None,
            hw_version=self.bridge.device.properties["hardware"],
            identifiers={(DOMAIN, self.bridge.device.uuid)},
            manufacturer=manufacturer,
            model=model,
            name=self.bridge.device.name,
            suggested_area=None,
            sw_version=self.bridge.device.properties["firmware"],
            via_device=(DOMAIN, DOMAIN)
        )

    @property
    def group_members(self) -> list[str]:
        multiroom = get_active_multiroom(self.hass, self.bridge)
        if multiroom is not None:
            return [multiroom.leader.device.uuid] + [follower.device.uuid for follower in multiroom.followers]

        return []

    async def async_update(self):
        """Update the state of the media player."""
        try:
            await self.bridge.player.update_status()
            self._update_properties()
        except Exception as e:
            _LOGGER.error(e)
            self._attr_available = False

    async def async_select_source(self, source: str) -> None:
        await self.bridge.player.set_play_mode(SOURCE_MAP_INV[source])

    async def async_select_sound_mode(self, sound_mode: str):
        """Switch the sound mode of the entity."""
        await self.bridge.player.set_equalizer_mode(EQUALIZER_MAP_INV[sound_mode])

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

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Set repeat mode."""
        await self.bridge.player.set_loop_mode(REPEAT_MAP_INV[repeat])

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        # If your media player has no own media sources to browse, route all browse commands
        # to the media source integration.
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            # This allows filtering content. In this case it will only show audio sources.
            content_filter=lambda item: item.media_content_type.startswith("audio/"),
        )

    async def async_play_media(self, media_type: str, media_id: str, **kwargs) -> None:
        """Play a piece of media."""

        ab = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
        await self.bridge.player.play(ab.url)

    async def async_join_players(self, group_members: list[str]) -> None:
        """Join `group_members` as a player group with the current player."""

        controller: LinkPlayController = self.hass.data[DOMAIN][CONTROLLER]
        multiroom = get_active_multiroom(self.hass, self.bridge)
        if multiroom.leader is None:
            multiroom = LinkPlayMultiroom(self.bridge)

        for group_member in group_members:
            bridge = next((bridge for bridge in self.controller.bridges if bridge.device.uuid == group_member), None)
            await multiroom.add_follower(bridge)

        await controller.discover_multirooms()

    async def async_unjoin_player(self) -> None:
        """Remove this player from any group."""

        multiroom = get_active_multiroom(self.hass, self.bridge)
        if multiroom is not None:
            multiroom.remove_follower(self.bridge)

    def _update_properties(self) -> None:
        """Update the properties of the media player."""
        self._attr_available = True
        self._attr_state = STATE_MAP[self.bridge.player.status]
        self._attr_volume_level = self.bridge.player.volume / 100
        self._attr_is_volume_muted = self.bridge.player.muted
        self._attr_repeat = REPEAT_MAP[self.bridge.player.loop_mode]
        self._attr_shuffle = self.bridge.player.loop_mode == LoopMode.RANDOM_PLAYBACK
        self._attr_sound_mode = EQUALIZER_MAP[self.bridge.player.equalizer_mode]
        self._attr_supported_features = DEFAULT_FEATURES

        if self.bridge.player.status == PlayingStatus.PLAYING:
            if self.bridge.player.total_length != 0:
                self._attr_supported_features = self._attr_supported_features | SEEKABLE_FEATURES

            if self.bridge.player.play_mode in SOURCE_MAP:
                self._attr_source = SOURCE_MAP[self.bridge.player.play_mode]
            else:
                self._attr_source = "other"

            self._attr_media_position = self.bridge.player.current_position / 1000
            self._attr_media_position_updated_at = utcnow()
            self._attr_media_duration = self.bridge.player.total_length / 1000
            self._attr_media_artist = self.bridge.player.artist
            self._attr_media_title = self.bridge.player.title
            self._attr_media_album_name = self.bridge.player.album
        elif self.bridge.player.status == PlayingStatus.STOPPED:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
            self._attr_media_artist = None
            self._attr_media_title = None
            self._attr_media_album_name = None
            self._attr_media_content_type = None
