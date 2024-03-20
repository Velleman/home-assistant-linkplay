"""The LinkPlay integration."""
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from linkplay.discovery import discover_linkplay_bridges

from .const import DOMAIN, PLATFORMS, DISCOVERY_SCAN_INTERVAL, BRIDGE_DISCOVERED, BRIDGE_UUIDS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Async setup hass config entry. Called when an entry has been setup."""

    hass.data.setdefault(DOMAIN, {BRIDGE_UUIDS: []})
    session = async_get_clientsession(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _async_scan_update(_=None):
        bridges = await discover_linkplay_bridges(session)

        for bridge in bridges:
            if bridge.device.uuid not in hass.data[DOMAIN][BRIDGE_UUIDS]:
                hass.data[DOMAIN][BRIDGE_UUIDS].append(bridge.device.uuid)
                async_dispatcher_send(hass, BRIDGE_DISCOVERED, bridge)

    await _async_scan_update()

    entry.async_on_unload(
        async_track_time_interval(
            hass, _async_scan_update, timedelta(seconds=DISCOVERY_SCAN_INTERVAL)
        )
    )

    return True
