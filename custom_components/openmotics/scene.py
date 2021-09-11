"""Support for HomeAssistant scenes (aka group actions)."""
# from __future__ import annotations
from typing import Any, Generic, TypeVar

import logging

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .openmotics_device import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scenes for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for om_scene in coordinator.data["scene"]:
        if (
            om_scene["name"] is None
            or om_scene["name"] == ""
            or om_scene["name"] == NOT_IN_USE
        ):
            continue
        # print("- {}".format(om_scene))
        entities.append(OpenMoticsScene(coordinator, om_scene))

    if not entities:
        _LOGGER.info("No OpenMotics Group Actions (Scenes) added")
        return False

    async_add_entities(entities)


class OpenMoticsScene(OpenMoticsDevice, Scene):
    """Representation of a OpenMotics group action."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, om_scene):
        """Initialize the scene."""
        super().__init__(coordinator, om_scene, "scene")
        self.coordinator = coordinator

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.hass.async_add_executor_job(
            self.coordinator.backenclient.otrigger_scene,
            self.install_id,
            self.device_id,
        )
