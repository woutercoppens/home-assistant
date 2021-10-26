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
from typing import Any, Generic, TypeVar

# import async_timeout
from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.config_entries import SOURCE_IMPORT  # Needed for config_flow
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant

# from homeassistant.core import Config, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

# from homeassistant.helpers.entity import Entity
# from homeassistant.helpers.typing import ConfigType
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
# from openmotics.clients.cloud import APIError, BackendClient
# from openmotics.clients.cloud import BackendClient
# from openmotics.clients.error import APIError

import voluptuous as vol

from .const import (
    CONF_INSTALLATION_ID,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import OpenMoticsDataUpdateCoordinator
from .exceptions import CannotConnect

# from openmotics.clients.exceptions import APIException

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_CLIENT_ID, "auth"): cv.string,
                vol.Optional(CONF_CLIENT_SECRET, "auth"): cv.string,
                vol.Optional(CONF_HOST, default=DEFAULT_HOST):
                # vol.All(cv.string, is_socket_address),
                cv.string,
                vol.Optional(CONF_INSTALLATION_ID, "auth"): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)


# async def async_setup_entry(
#     hass: core.HomeAssistant, config: config_entries.ConfigEntry
# ):
#     """
#     Openmotics uses config flow for configuration.

#     But, an "openmotics:" entry in configuration.yaml will trigger an import
#     flow if a config entry doesn't already exist.
#     """
#     if DOMAIN not in config:
#         return True

#     conf = config[DOMAIN]
#     hass.data[DATA_OPENMOTICS_CONFIG] = conf

#     if hass.config_entries.async_entries(DOMAIN):
#         _LOGGER.debug("Config entries exists.")

#     if (
#         not hass.config_entries.async_entries(DOMAIN)
#         and hass.data[DATA_OPENMOTICS_CONFIG]
#     ):
#         # No config entry exists and configuration.yaml config exists, trigger the import flow.
#         hass.async_create_task(
#             hass.config_entries.flow.async_init(
#                 DOMAIN,
#                 context={"source": SOURCE_IMPORT},
#                 data={
#                     CONF_HOST: conf.get(CONF_HOST, DEFAULT_HOST),
#                     CONF_CLIENT_ID: conf.get(CONF_CLIENT_ID),
#                     CONF_CLIENT_SECRET: conf.get(CONF_CLIENT_SECRET),
#                     CONF_INSTALL_ID: conf.get(CONF_INSTALL_ID),
#                     CONF_PORT: conf.get(CONF_PORT, DEFAULT_PORT),
#                     CONF_VERIFY_SSL: conf.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
#                 },
#             )
#         )

#     return True


async def async_setup_openmotics_installation(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, openmotics_installation
):
    """Set up the OpenMotics Installation."""
    # entry_id = entry.entry_id
    # hass.data[DOMAIN].setdefault(entry_id, {})

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, openmotics_installation["id"])},
        manufacturer="OpenMotics",
        name=openmotics_installation["name"],
        model=openmotics_installation["gateway_model"],
        sw_version=openmotics_installation["version"],
    )

    return True


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    """Set up OpenMotics Gateway from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    """Set up OpenMotics from a config entry."""
    coordinator = OpenMoticsDataUpdateCoordinator(hass, entry=entry)
    await coordinator.async_config_entry_first_refresh()

    if not await coordinator.get_token():
        raise ConfigEntryNotReady(f"Unable to connect to OpenMoticsApi")

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady(f"Unable to connect to OpenMoticsApi")

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up all platforms for this device/entry.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry)
        hass.data.pop(DOMAIN)

    return unload_ok
