"""The LinkPlay integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.config import ConfigType
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS

async def async_setup(hass: HomeAssistant, config_type: ConfigType):
    """Async setup of integration."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Async setup hass config entry. Called when an entry has been setup."""

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
