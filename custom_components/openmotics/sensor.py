"""Support for HomeAssistant lights."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    # ATTR_BATTERY_LEVEL,
    ATTR_TEMPERATURE,
    # DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    # DEVICE_CLASS_POWER,
    # DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    # LIGHT_LUX,
    PERCENTAGE,
    # POWER_WATT,
    # PRESSURE_HPA,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .openmotics_device import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)

ATTR_HUMIDITY = "humidity"
ATTR_ILLUMINANCE = "illuminance"


@dataclass
class OpenMoticsSensorDescription(SensorEntityDescription):
    """Class that holds device specific info for a openmotics sensor."""

    attributes: tuple = ()


SENSOR_TYPES = {
    ATTR_TEMPERATURE: OpenMoticsSensorDescription(
        key=ATTR_TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    ATTR_HUMIDITY: OpenMoticsSensorDescription(
        key=ATTR_HUMIDITY,
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_HUMIDITY,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    ATTR_ILLUMINANCE: OpenMoticsSensorDescription(
        key=ATTR_ILLUMINANCE,
        name="Illuminance",
        native_unit_of_measurement=PERCENTAGE,
        device_class=DEVICE_CLASS_ILLUMINANCE,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sensors for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for om_sensor in coordinator.data["sensors"]:
        if (
            om_sensor["name"] is None
            or om_sensor["name"] == ""
            or om_sensor["name"] == NOT_IN_USE
        ):
            continue
        # if om_sensor["physical_quantity"] == "temperature":
        #     entities.append(OpenMoticsLight(coordinator, om_sensor, "Temperature"))

    if not entities:
        _LOGGER.info("No OpenMotics sensors added")
        return False

    async_add_entities(entities)


class OpenMoticsSensor(OpenMoticsDevice, SensorEntity):
    """Representation of a OpenMotics light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        om_sensor,
        description: SensorEntityDescription,
    ):
        """Initialize the light."""
        super().__init__(coordinator, om_sensor, "sensor")
        self.coordinator = coordinator
        self.entity_description = description
        self.sensor_name = om_sensor["name"]
        self._state = None

        self._attr_name = f"{self.sensor_name} {description.name}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._state in ("unknown",):
            return None

        return self._state

    async def async_update(self):
        """Refresh the state of the light."""
        for om_sensor in self.coordinator.data["sensors"]:
            if om_sensor["id"] == self.device_id:
                if om_sensor["status"] is not None:
                    self._state = om_sensor["status"]
                else:
                    self._state = None
