"""Support for HomeAssistant switches."""
from __future__ import annotations

import logging

from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.const import STATE_OFF, STATE_ON
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
    """Set up Switches for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for om_outlet in coordinator.data["outlet"]:
        if (
            om_outlet["name"] is None
            or om_outlet["name"] == ""
            or om_outlet["name"] == NOT_IN_USE
        ):
            continue
        entities.append(OpenMoticsSwitch(coordinator, om_outlet))

    if not entities:
        _LOGGER.info("No OpenMotics Outlets added")
        return False

    async_add_entities(entities)


class OpenMoticsSwitch(OpenMoticsDevice, SwitchEntity):
    """Representation of a OpenMotics switch."""

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, om_switch):
        """Initialize the switch."""
        super().__init__(coordinator, om_switch, "switch")
        self.coordinator = coordinator

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    async def async_turn_on(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(
            self.coordinator.backenclient.output_turn_on,
            self.install_id,
            self.device_id,
        )

        # await self.coordinator._async_update_data()

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(
            self.coordinator.backenclient.output_turn_off,
            self.install_id,
            self.device_id,
        )

        # await self.coordinator._async_update_data()

    async def async_update(self):
        """Refresh the state of the switch."""
        for om_outlet in self.coordinator.data["outlet"]:
            if om_outlet["id"] == self.device_id:
                if om_outlet["status"] is not None:
                    status = om_outlet["status"]
                    if status["on"] is True:
                        self._state = STATE_ON
                    else:
                        self._state = STATE_OFF
                else:
                    self._state = None
