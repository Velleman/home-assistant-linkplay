from typing import Any
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN, CONF_IP


class LinkPlayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """LinkPlay config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        # Specify items in the order they are to be displayed in the UI
        data_schema = vol.Schema({
            vol.Required(CONF_IP): str
        })

        if user_input:
            # Return the form of the next step
            return self.async_create_entry(title="LinkPlay", data=user_input)

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_ssdp(self, info):
        pass

    async def async_finish_flow(flow, result):
        """Finish flow."""
        pass