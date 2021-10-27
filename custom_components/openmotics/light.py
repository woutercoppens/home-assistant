"""Support for HomeAssistant lights."""
from __future__ import annotations

import logging
from typing import ValuesView

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .entity import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lights for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for om_light in coordinator.data["outputs"]:
        if (
            om_light["name"] is None
            or om_light["name"] == ""
            or om_light["name"] == NOT_IN_USE
        ):
            continue

        # Outputs can contain outlets and lights, so filter out only the lights
        if om_light["type"] == "LIGHT":
            # print("- {}".format(om_light))
            entities.append(OpenMoticsOutputLight(coordinator, om_light))

    if not entities:
        _LOGGER.info("No OpenMotics Lights added")
        return False

    async_add_entities(entities)


def brightness_to_percentage(byt):
    """Convert brightness from absolute 0..255 to percentage."""
    return round((byt * 100.0) / 255.0)


def brightness_from_percentage(percent):
    """Convert percentage to absolute value 0..255."""
    return round((percent * 255.0) / 100.0)


class OpenMoticsOutputLight(OpenMoticsDevice, LightEntity):
    """Representation of a OpenMotics light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, om_light):
        """Initialize the light."""
        super().__init__(coordinator, om_light, "light")
        self.coordinator = coordinator
        self._brightness = None

    @property
    def supported_features(self):
        """Flag supported features."""
        # Check if the light's module is a Dimmer, return brightness as a supported feature.
        if "RANGE" in self._device["capabilities"]:
            return SUPPORT_BRIGHTNESS

        return 0

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self._brightness

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        if brightness is None:
            response = await self.hass.async_add_executor_job(
                self.coordinator.backenclient.base.installations.outputs.turn_on,
                self.install_id,
                self.device_id,
            )
        else:
            # Openmotics brightness (value) is between 0..100
            response = await self.hass.async_add_executor_job(
                self.coordinator.backenclient.base.installations.outputs.turn_on,
                self.install_id,
                self.device_id,
                brightness_to_percentage(brightness), #value
            )

        # Turns on a specified Output object.
        # The call can optionally receive a JSON object that states the value
        # in case the Output is dimmable.
        if response:
            try:
                self._brightness = brightness_from_percentage(response["value"])
            except KeyError:
                self._brightness = None
        self._state = STATE_ON
        await self.coordinator.async_request_refresh()
        # await self.coordinator.async_refresh()
        
    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(
            self.coordinator.backenclient.base.installations.outputs.turn_off,
            self.install_id,
            self.device_id,
        )
        self._state = STATE_OFF
        await self.coordinator.async_request_refresh()
        # await self.coordinator.async_refresh()

    async def async_update(self):
        """Refresh the state of the light."""
        for om_light in self.coordinator.data["outputs"]:
            if om_light["id"] == self.device_id:
                if om_light["status"] is not None:
                    status = om_light["status"]
                    if status["on"] is True:
                        self._state = STATE_ON
                    else:
                        self._state = STATE_OFF
                    # if a light is not dimmable, the value field is not present.
                    try:
                        self._brightness = brightness_from_percentage(status["value"])
                    except KeyError:
                        self._brightness = None
                else:
                    self._state = None
