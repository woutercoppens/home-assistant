"""Generic OpenMoticDevice Enity."""
from __future__ import annotations

# from abc import abstractmethod

# from typing import Any, Generic, TypeVar

from homeassistant.helpers.entity import Entity
# from homeassistant.helpers.typing import ConfigType

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
# from homeassistant.helpers.restore_state import RestoreEntity

# from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import OpenMoticsDataUpdateCoordinator


class OpenMoticsDevice(CoordinatorEntity, Entity):
    """Representation a base OpenMotics device."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator,
        device,
        device_type,
    ) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self.backendclient = coordinator.backendclient
        self._install_id = coordinator.install_id
        self._is_available = True
        self._device = device
        self._sid = device["id"]
        self._name = device["name"]
        self._type = device_type
        self._state = None
        self._extra_state_attributes = {}
        # Because polling is so common, Home Assistant by default assumes that your entity is based on polling.
        # But it's set anyway to True
        self._poll: bool = True

    @property
    def should_poll(self)-> bool:
        """Enable polling."""
        return self._poll

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def floor(self) -> str:
        """Return the floor of the device."""
        location = self._device["location"]
        try:
            return location["floor_id"]
        except KeyError:
            return "N/A"

    @property
    def is_on(self)-> bool:
        """Return true if switch is on."""
        return self._state

    @property
    def room(self) -> str:
        """Return the room of the device."""
        location = self._device["location"]
        try:
            return location["room_id"]
        except KeyError:
            return "N/A"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.install_id}-{self.device_id}"

    @property
    def device_id(self) -> str:
        """Return a unique ID."""
        return self._sid

    @property
    def type(self) -> str:
        """Return a unique ID."""
        return self._type


    @property
    def install_id(self):
        """Return the installation ID."""
        return self._install_id

    @property
    def available(self) -> bool:
        """If device is available."""
        # return self._state is not None
        return self._is_available

    @property
    def device_info(self)-> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self._name,
            id=self._sid,
            installation=self._install_id,
            manufacturer="OpenMotics",
        )

    # async def _async_update_callback(self) -> None:
    #     """Update the entity."""
    #     await self.async_update_ha_state(True)
