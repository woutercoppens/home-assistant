"""Support for HomeAssistant switches."""
import logging

from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.core import callback
from homeassistant.const import STATE_OFF, STATE_ON

from . import OpenMoticsDevice
from .const import (DOMAIN, NOT_IN_USE)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Switches for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_outlets = await hass.async_add_executor_job(om_cloud.outlets, install_id)
        if om_outlets:
            for om_outlet in om_outlets:
                if (om_outlet['name'] is None or om_outlet['name'] == "" or om_outlet['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_outlet))
                entities.append(OpenMoticsSwitch(hass, om_cloud, install, om_outlet))

    if not entities:
        _LOGGER.warning("No OpenMotics Outlets added")
        return False

    async_add_entities(entities)


class OpenMoticsSwitch(OpenMoticsDevice, SwitchEntity):
    """Representation of a OpenMotics switch."""

    def __init__(self, hass, om_cloud, install, om_switch):
        """Initialize the switch."""
        self._hass = hass
        self.om_cloud = om_cloud
        super().__init__(install, om_switch, 'switch' )
        
    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self.hass.async_add_executor_job(self.om_cloud.output_turn_on, self.install_id, self.unique_id)

        self.async_update

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(self.om_cloud.output_turn_off, self.install_id, self.unique_id)

        self.async_update

    async def async_update(self):
        """Update the state of the switch."""
        output_status = await self.hass.async_add_executor_job(self.om_cloud.output_by_id, self.install_id, self.unique_id)

        if not output_status:
            _LOGGER.error('Light._refresh: No responce form the controller')
            return
        # print("- {}".format(output_status))

        if output_status['status'] is not None:
            status = output_status['status']
            if status['on'] is True:
                self._state = STATE_ON
            else:
                self._state = STATE_OFF
        else:
            self._state = None