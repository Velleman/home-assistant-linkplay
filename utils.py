from homeassistant.core import HomeAssistant
from linkplay.bridge import LinkPlayBridge, LinkPlayMultiroom
from linkplay.controller import LinkPlayController

from .const import DOMAIN, CONTROLLER

def get_active_multiroom(hass: HomeAssistant, bridge: LinkPlayBridge) -> LinkPlayMultiroom | None:
    """Get the active multiroom for given bridge."""

    controller: LinkPlayController = hass.data[DOMAIN][CONTROLLER]

    for multiroom in controller.multirooms:
        if multiroom.leader.device.uuid == bridge.device.uuid:
            return multiroom

        for follower in multiroom.followers:
            if follower.device.uuid == bridge.device.uuid:
                return multiroom

    return None
