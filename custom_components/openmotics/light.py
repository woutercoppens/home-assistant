"""Support for HomeAssistant lights."""
from __future__ import annotations

import logging

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
    """Set up Lights for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for om_light in coordinator.data["lights"]:
        if (
            om_light["name"] is None
            or om_light["name"] == ""
            or om_light["name"] == NOT_IN_USE
        ):
            continue
        # print("- {}".format(om_light))
        entities.append(OpenMoticsLight(coordinator, om_light))

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


class OpenMoticsLight(OpenMoticsDevice, LightEntity):
    """Representation of a OpenMotics light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, om_light):
        """Initialize the light."""
        super().__init__(coordinator, om_light, "light")
        self.coordinator = coordinator
        self._brightness: Optional[int] = None

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
        """Return the brightness of this light."""
        return self._brightness

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        value: Optional[int] = None
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            if brightness is not None:
                value = brightness_to_percentage(brightness)
        else:
            brightness = 100

        response = await self.hass.async_add_executor_job(
            self.coordinator.backenclient.base.installations.outputs.turn_on,
            self.install_id,
            self.device_id,
            brightness,
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
        self.schedule_update_ha_state()
        # await self.coordinator._async_update_data()

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(
            self.coordinator.backenclient.base.installations.outputs.turn_off,
            self.install_id,
            self.device_id,
        )
        self._state = STATE_OFF
        self.schedule_update_ha_state()
        # await self.coordinator._async_update_data()

    async def async_update(self):
        """Refresh the state of the light."""
        for om_light in self.coordinator.data["light"]:
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
