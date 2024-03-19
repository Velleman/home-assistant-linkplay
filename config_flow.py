from typing import Any
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.components.ssdp import SsdpServiceInfo
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from linkplay.discovery import linkplay_factory_bridge
from linkplay.bridge import LinkPlayBridge
import voluptuous as vol



from .const import DOMAIN, CONF_IP

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_IP): str
})
_LOGGER = logging.getLogger(__name__)


class LinkPlayConfigFlow(ConfigFlow, domain=DOMAIN):
    """LinkPlay config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    _discovery_ip: str

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        
        if not user_input:
            return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

        bridge = await self._verify_linkplay(user_input[CONF_IP])
        if bridge is None:
            return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, user_input=user_input, errors={"base": "cannot_connect"})

        await self.async_set_unique_id(bridge.device.uuid)
        self._abort_if_unique_id_configured(user_input)
        return self.async_create_entry(title="LinkPlay", data=user_input)

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        self._discovery_ip = discovery_info.ssdp_server
        return self.async_show_form(step_id="discovery_confirm")

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        """Handle a flow initialized by Zeroconf discovery."""
        self._discovery_ip = discovery_info.ip_address
        return self.async_show_form(step_id="discovery_confirm")

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None):
        """Handle the confirmation step."""
        
        if user_input is not None:
            return self.async_create_entry(title="LinkPlay", data=user_input)

        bridge = await self._verify_linkplay(self._discovery_ip)
        if bridge is None:
            return None
        
        await self.async_set_unique_id(bridge.device.uuid)
        model = {CONF_IP: self._discovery_ip}
        self._abort_if_unique_id_configured(model)
        self._set_confirm_only()
        return self.async_show_form(step_id="discovery_confirm", description_placeholders=model)

    async def _verify_linkplay(self, ip: str) -> LinkPlayBridge | None:
        try:
            return await linkplay_factory_bridge(ip, async_get_clientsession(self.hass))
        except Exception as e:
            _LOGGER.error(e)
        
        return None
