from typing import Any
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.components.ssdp import SsdpServiceInfo, ATTR_UPNP_FRIENDLY_NAME
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_NAME
from linkplay.discovery import linkplay_factory_bridge
from linkplay.bridge import LinkPlayBridge
import voluptuous as vol



from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str
})
_LOGGER = logging.getLogger(__name__)


class LinkPlayConfigFlow(ConfigFlow, domain=DOMAIN):
    """LinkPlay config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        
        if not user_input:
            return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

        self.context[CONF_HOST] = user_input[CONF_HOST]
        await self._verify_device()
        return self.async_create_entry(title=self.context[CONF_NAME], data=user_input)

    # async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
    #     """Handle a flow initialized by SSDP discovery."""
    #     self.context[CONF_HOST] = discovery_info.ssdp_location
    #     return self.async_show_form(step_id="discovery_confirm")

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        """Handle a flow initialized by Zeroconf discovery."""
        self.context[CONF_HOST] = str(discovery_info.ip_address)
        await self._verify_device()
        return self.async_show_form(step_id="discovery_confirm")

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle user-confirmation of discovered device."""
        if user_input is not None:
            return self.async_create_entry(title=self.context[CONF_NAME], data=self.context)

        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm", 
            description_placeholders={"name": self.context[CONF_NAME]})

    async def _verify_device(self) -> None:
        try:
            bridge = await linkplay_factory_bridge(self.context[CONF_HOST], async_get_clientsession(self.hass))
            self.context[CONF_NAME] = bridge.device.name
            await self.async_set_unique_id(bridge.device.uuid)
            self._abort_if_unique_id_configured(self.context)

        except Exception as e:
            _LOGGER.error(e)
            raise AbortFlow("cannot_connect")