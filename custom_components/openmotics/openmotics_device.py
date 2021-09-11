"""Generic OpenMoticDevice Enity."""
from __future__ import annotations

# from abc import abstractmethod

# from typing import Any, Generic, TypeVar

# from homeassistant.helpers.entity import Entity
# from homeassistant.helpers.typing import ConfigType


# from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

# from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import OpenMoticsDataUpdateCoordinator


class OpenMoticsDevice(CoordinatorEntity):
    """Representation a base OpenMotics device."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator, device, device_type) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self.backendclient = coordinator.backendclient
        self._install_id = coordinator.install_id
        self._is_available = True
        self._device = device
        self._sid = device["id"]
        self._type = device_type
        self._state = None
        self._extra_state_attributes = {}
        self._poll: bool = True

    @property
    def should_poll(self):
        """Enable polling."""
        return self._poll

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device["name"]

    @property
    def floor(self):
        """Return the floor of the device."""
        location = self._device["location"]
        try:
            return location["floor_id"]
        except KeyError:
            return "N/A"

    @property
    def room(self):
        """Return the room of the device."""
        location = self._device["location"]
        try:
            return location["room_id"]
        except KeyError:
            return "N/A"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.install_id}-{self._sid}"

    @property
    def device_id(self) -> str:
        """Return a unique ID."""
        return self._sid

    @property
    def install_id(self):
        """Return the installation ID."""
        return self._install_id

    @property
    def available(self):
        """If device is available."""
        # return self._state is not None
        return self._is_available

    @property
    def device_info(self):
        """Return information about the device."""
        if self._type in ("scene", "cover"):
            # Scenes and floor don't have the floor and room property
            return {
                "identifiers": {(DOMAIN, self.unique_id)},
                "name": self.name,
                "id": self.unique_id,
                "installation": self.install_id,
                "manufacturer": "OpenMotics",
            }
        else:
            return {
                "identifiers": {(DOMAIN, self.unique_id)},
                "name": self.name,
                "id": self.unique_id,
                "floor": self.floor,
                "room": self.room,
                "installation": self.install_id,
                "manufacturer": "OpenMotics",
            }
