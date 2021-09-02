"""The Openmotics integration.

    Support for OpenMotics.
    For more details about this component, please refer to the documentation at
    https://github.com/openmotics/home-assistant

    For examples of the output of the api, look at openmotics_api.md
"""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import async_timeout
from typing import Any, Generic, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import voluptuous as vol
from homeassistant.core import callback
from homeassistant import config_entries, core
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import \
    SOURCE_IMPORT  # Needed for config_flow
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PORT,
    CONF_HOST,
    CONF_VERIFY_SSL,
)

from .const import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)

from openmotics.clients.cloud import BackendClient, APIError
# from openmotics.clients.exceptions import APIException
# from var_dump import var_dump

from .exceptions import CannotConnect

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({
        vol.Optional(CONF_CLIENT_ID, 'auth'): cv.string,
        vol.Optional(CONF_CLIENT_SECRET, 'auth'): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST):
            # vol.All(cv.string, is_socket_address),
            cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_VERIFY_SSL,
                     default=DEFAULT_VERIFY_SSL): cv.boolean,
    })},
    extra=vol.ALLOW_EXTRA
    )

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: core.HomeAssistant, config: config_entries.ConfigEntry
):
    """
    Openmotics uses config flow for configuration.

    But, an "openmotics:" entry in configuration.yaml will trigger an import
    flow if a config entry doesn't already exist.
    """
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data[DATA_OPENMOTICS_CONFIG] = conf

    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.debug("Config entries exists.")

    if not hass.config_entries.async_entries(DOMAIN) and hass.data[DATA_OPENMOTICS_CONFIG]:
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_HOST: conf.get(CONF_HOST, DEFAULT_HOST),
                    CONF_CLIENT_ID: conf.get(CONF_CLIENT_ID),
                    CONF_CLIENT_SECRET: conf.get(CONF_CLIENT_SECRET),
                    CONF_PORT: conf.get(CONF_PORT, DEFAULT_PORT),
                    CONF_VERIFY_SSL: conf.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                },
            )
        )

    return True


async def async_setup_openmotics_installation(hass: core.HomeAssistant, entry: config_entries.ConfigEntry, openmotics_installation):
    """Set up the OpenMotics Installation."""
    # entry_id = entry.entry_id
    # hass.data[DOMAIN].setdefault(entry_id, {})

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, openmotics_installation['id'])},
        manufacturer="OpenMotics",
        name=openmotics_installation['name'],
        model=openmotics_installation['gateway_model'],
        sw_version=openmotics_installation['version'],
    )

    return True


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    """Set up OpenMotics Gateway from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    host = entry.data.get(CONF_HOST)
    client_id = entry.data.get(CONF_CLIENT_ID)
    client_secret = entry.data.get(CONF_CLIENT_SECRET)
    port = entry.data.get(CONF_PORT)
    verify_ssl = entry.data.get(CONF_VERIFY_SSL)

    """Set up a OpenMotics controller"""
    if host == DEFAULT_HOST:
        om_cloud = BackendClient(
            client_id,
            client_secret,
            )
    else:
        om_cloud = BackendClient(
            client_id,
            client_secret,
            server=host,
            port=port,
            ssl=verify_ssl
            )

    try:
        await hass.async_add_executor_job(om_cloud.get_token)
    except asyncio.TimeoutError:
        _LOGGER.error(
            "Timeout connecting to the OpenMoticsApi at %s",
            host
            )
        raise CannotConnect

    except APIError:
        _LOGGER.error(
            "Error connecting to the OpenMoticsApi at %s",
            host
            )
        # _LOGGER.error(err)
        raise CannotConnect

    hass.data[DOMAIN][entry.entry_id] = om_cloud

    om_installations = await hass.async_add_executor_job(om_cloud.installations)
    for install in om_installations:
        # print("- {}".format(install))
        await async_setup_openmotics_installation(hass, entry, install)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry,
                platform
                )
        )
    return True

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(
                    config_entry,
                    platform
                    )
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry)
        hass.data.pop(DOMAIN)

    return unload_ok


class OpenMoticsDevice(Entity):
    """Representation a base OpenMotics device."""

    def __init__(
        self, install, device, device_type
    ) -> None:
        """Initialize the device."""
        self._install_id = install['id']
        self._is_available = True
        self._device = device
        self._type = device_type
        self._state = None
        self._extra_state_attributes = {}
        self._poll: bool =  False

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates."""
        # self.om_cloud.register(self._device, self._update_callback)
        self._poll = True

    # def _update_callback(self, _device: DeviceType) -> None:
    #     """Update the state."""
    #     self.schedule_update_ha_state(True)

    @property
    def should_poll(self):
        """Enable polling."""
        return self._poll

    @property
    def name(self) -> str:
        """Return the name of the light."""
        return self._device['name']

    @property
    def floor(self):
        """Return the floor of the light."""
        location = self._device['location']
        return location['floor_id']

    @property
    def room(self):
        """Return the room of the light."""
        location = self._device['location']
        return location['room_id']

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._device['id']

    @property
    def install_id(self):
        """Return the installation ID."""
        return self._install_id

    @property
    def available(self):
        """If device is available."""
        return self._state is not None

    @property
    def device_info(self):
        """Return information about the device."""
        if self._type in ('scene', 'cover'):
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