""" Support for HomeAssistant scenes (aka group actions). """
# from var_dump import var_dump
import logging

from typing import Any
from homeassistant.components.scene import (
    Scene,
)
from homeassistant.core import callback

from . import OpenMoticsDevice
from .const import (DOMAIN, NOT_IN_USE)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Scenes for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_scenes = await hass.async_add_executor_job(om_cloud.groupactions, install_id)
        if om_scenes:
            for om_scene in om_scenes:
                if (om_scene['name'] is None or om_scene['name'] == "" or om_scene['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_scene))
                entities.append(OpenMoticsScene(hass, om_cloud, install, om_scene))

    if not entities:
        _LOGGER.warning("No OpenMotics scenes added")
        return False

    async_add_entities(entities)


class OpenMoticsScene(OpenMoticsDevice, Scene):
    """Representation of a OpenMotics group action."""

    def __init__(self, hass, om_cloud, install, om_scene):
        """Initialize the scene."""
        self._hass = hass
        self.om_cloud = om_cloud
        super().__init__(install, om_scene, 'scene' )


    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.hass.async_add_executor_job(self.om_cloud.trigger_scene, self.install_id, self.unique_id)