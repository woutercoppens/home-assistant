"""DataUpdateCoordinator for the OpenMotics integration."""
# from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from openmotics.clients.cloud import APIError, BackendClient

from .const import (
    CONF_INSTALLATION_ID,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .exceptions import CannotConnect, InvalidAuth

_LOGGER = logging.getLogger(__name__)


class OpenMoticsDataUpdateCoordinator(DataUpdateCoordinator):
    """A OpenMotics Data Update Coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the OpenMotics gateway."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # update_method=self._async_update_data,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.hass = hass
        # self.entry = entry
        self._install_id = entry.data.get(CONF_INSTALLATION_ID)

        """Set up a OpenMotics controller"""
        if entry.data.get(CONF_HOST) == DEFAULT_HOST:
            self.backendclient = BackendClient(
                client_id=entry.data.get(CONF_CLIENT_ID),
                client_secret=entry.data.get(CONF_CLIENT_SECRET),
            )
        else:
            self.backendclient = BackendClient(
                client_id=entry.data.get(CONF_CLIENT_ID),
                client_secret=entry.data.get(CONF_CLIENT_SECRET),
                server=entry.data.get(CONF_HOST),
                port=entry.data.get(CONF_PORT),
                ssl=entry.data.get(CONF_VERIFY_SSL),
            )

    async def get_token(self) -> bool:
        """Login to OpenMotics cloud / gateway."""
        try:
            await self.hass.async_add_executor_job(self.backendclient.get_token)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout connecting to the OpenMoticsApi")
            raise CannotConnect

        except APIError:
            _LOGGER.error("Error connecting to the OpenMoticsApi")
            # _LOGGER.error(err)
            raise CannotConnect

        return True

    async def _async_update_data(self) -> dict:
        """Fetch data from OpenMotics."""

        try:
            om_lights = await self.hass.async_add_executor_job(
                self.backendclient.lights, self.install_id
            )
            om_outlets = await self.hass.async_add_executor_job(
                self.backendclient.outlets, self.install_id
            )
            om_scenes = await self.hass.async_add_executor_job(
                self.backendclient.groupactions, self.install_id
            )
            om_covers = await self.hass.async_add_executor_job(
                self.backendclient.shutters, self.install_id
            )

        except APIError:
            _LOGGER.error("Error retrieving the lights")
            raise

        # Store data in a way Home Assistant can easily consume it
        return {
            "light": om_lights,
            "outlet": om_outlets,
            "scene": om_scenes,
            "cover": om_covers,
            #     "ethernet": overview.get("ethernetConnectedNow"),
            #     "cameras": {
            #         device["deviceLabel"]: device
            #         for device in overview["customerImageCameras"]
            #     },
            #     "climate": {
            #         device["deviceLabel"]: device for device in overview["climateValues"]
            #     },
            #     "door_window": {
            #         device["deviceLabel"]: device
            #         for device in overview["doorWindow"]["doorWindowDevice"]
            #     },
            #     "locks": {
            #         device["deviceLabel"]: device
            #         for device in overview["doorLockStatusList"]
            #     },
            #     "mice": {
            #         device["deviceLabel"]: device
            #         for device in overview["eventCounts"]
            #         if device["deviceType"] == "MOUSE1"
            #     },
            #     "smart_plugs": {
            #         device["deviceLabel"]: device for device in overview["smartPlugs"]
            #     },
        }

    @property
    def install_id(self) -> str:
        """Return the name of the device."""
        return self._install_id

    @property
    def backenclient(self) -> str:
        """Return the backendclient."""
        return self.backendclient


# async def get_backendclient(hass, client_id, client_secret, server, port, ssl):
#     """Create a backendclient object and verify authentication."""
#     if server == DEFAULT_HOST:
#         backendclient = BackendClient(
#             client_id=client_id,
#             client_secret=client_secret,
#         )
#     else:
#         backendclient = BackendClient(
#             client_id=client_id,
#             client_secret=client_secret,
#             server=server,
#             port=port,
#             ssl=ssl,
#         )
#     try:
#         with async_timeout.timeout(10):
#              await backendclient.get_token()
#         # await hass.async_add_executor_job(backendclient, get_token)
#         _LOGGER.debug("returning backendclient")
#         return backendclient

#     except (
#         asyncio.TimeoutError,
#         APIError,
#     ) as err:
#         _LOGGER.error(err)
#         raise CannotConnect from err

#     except KeyError as err:
#         raise InvalidAuth from err

#     except RuntimeError as err:
#         raise CannotConnect from err

#     except InvalidClientError as err:
#         raise InvalidAuth from err
