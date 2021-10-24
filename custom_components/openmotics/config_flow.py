"""Adds config flow for OpenMotics."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_HOST,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from oauthlib.oauth2.rfc6749.errors import InvalidClientError
from pyopenmotics.openmotics import BackendClient
from pyopenmotics.exceptions import OpenMoticsError

from .const import (
    CONF_INSTALLATION_ID,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

# from .coordinator import get_backendclient
from .exceptions import CannotConnect, InvalidAuth


BACKENDCLIENT_CONFIG = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class OpenMoticsFlowHandler(config_entries.ConfigFlow):
    """Handle a config flow for OpenMotics."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Create a new instance of the flow handler."""
        self.config = {}
        self.installation_id = None
        self.installations = {}
        self.clientid = None
        self.client_secret = None

    async def async_step_import(self, user_input=None):
        """Occurs when a previously entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)

    def async_show_form_step_user(self, errors):
        """Show the form belonging to the user step."""
        schema = BACKENDCLIENT_CONFIG
        if (self.clientid is None and self.client_secret is None) or errors:
            schema = BACKENDCLIENT_CONFIG

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_user(self, user_input=None):
        # """Handle external yaml configuration."""
        # if self._async_current_entries():
        #     _LOGGER.warning("Only one configuration of OpenMotics is allowed.")
        #     return self.async_abort(reason="single_instance_allowed")
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:

            self.config = {
                CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
                CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
            }

            try:
                # Create a backendclient object and verify authentication.
                if self.config[CONF_HOST] == DEFAULT_HOST:
                    backendclient = BackendClient(
                        client_id=self.config[CONF_CLIENT_ID],
                        client_secret=self.config[CONF_CLIENT_SECRET],
                    )
                else:
                    backendclient = BackendClient(
                        client_id=self.config[CONF_CLIENT_ID],
                        client_secret=self.config[CONF_CLIENT_SECRET],
                        server=self.config[CONF_HOST],
                        port=self.config[CONF_PORT],
                        ssl=self.config[CONF_VERIFY_SSL],
                    )
                await self.hass.async_add_executor_job(backendclient.get_token)

                self.installations = await self.hass.async_add_executor_job(
                    backendclient.base.installations.all
                )

            # TODO: add proper error handling
            except (
                asyncio.TimeoutError,
                APIError,
            ) as err:
                _LOGGER.error(err)
                raise CannotConnect from err

            except KeyError as err:
                raise InvalidAuth from err
            except RuntimeError as err:
                raise CannotConnect from err
            except InvalidClientError as err:
                raise InvalidAuth from err
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            if errors:
                return self.async_show_form_step_user(errors)

        if len(self.installations) > 0:
            # show selection form
            return await self.async_step_select_installation()

        errors["base"] = "discovery_error"
        return self.async_show_form_step_user(errors)

    async def async_step_select_installation(self, user_input=None):
        """Ask user to select the Installation ID to use."""
        if user_input is None or CONF_INSTALLATION_ID not in user_input:
            # Get available installations
            existing_installations = [
                entry.data[CONF_INSTALLATION_ID]
                for entry in self._async_current_entries()
            ]

            installations_options = {
                installation["id"]: installation["name"]
                for installation in self.installations
                if installation["id"] not in existing_installations
            }
            if not installations_options:
                return self.async_abort(reason="no_available_installation")

            return self.async_show_form(
                step_id="select_installation",
                data_schema=vol.Schema(
                    {vol.Required(CONF_INSTALLATION_ID): vol.In(installations_options)}
                ),
            )

        self.installation_id = user_input[CONF_INSTALLATION_ID]
        return await self.async_step_create_entry()

    async def async_step_create_entry(self, data=None):
        """Create a config entry at completion of a flow and authorization of the app."""
        data = {
            CONF_HOST: self.config[CONF_HOST],
            CONF_CLIENT_ID: self.config[CONF_CLIENT_ID],
            CONF_CLIENT_SECRET: self.config[CONF_CLIENT_SECRET],
            CONF_INSTALLATION_ID: self.installation_id,
            CONF_PORT: self.config[CONF_PORT],
            CONF_VERIFY_SSL: self.config[CONF_VERIFY_SSL],
        }

        unique_id = self.construct_unique_id(
            self.config[CONF_HOST], self.installation_id
        )
        await self.async_set_unique_id(unique_id)

        return self.async_create_entry(title=unique_id, data=data)

    @staticmethod
    def construct_unique_id(host: str, install_id: str) -> str:
        """Construct the unique id from the ssdp discovery or user_step."""
        return f"{host}-{install_id}"
