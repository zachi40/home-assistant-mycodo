import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Mycodo switches."""
    mycodo_client = hass.data[DOMAIN]["client"]
    switches = await hass.async_add_executor_job(mycodo_client.get_switches)
    #  switches_output =  self.utils.mycodo_send("/api/outputs/")
    #  switches=switches_output.get('output devices', [])

    if not switches or "output devices" not in switches:
        _LOGGER.error("Failed to fetch switches from Mycodo.")
        return
    switches_states = switches.get("output states", [])

    switch_entities = []
    output_devices = switches.get("output devices", []) or []
    for switch in output_devices:
        state = switches_states.get(switch["unique_id"])
        switch_entities.append(
            MycodoSwitch(
                mycodo_client,
                switch["name"],
                switch["unique_id"],
                state["0"] == "on",
            )
        )

    async_add_entities(switch_entities)


class MycodoSwitch(SwitchEntity):
    """Representation of a Mycodo Switch."""

    def __init__(self, mycodo_client, name, unique_id, is_on):
        """Initialize the switch."""
        self._client = mycodo_client
        self._name = f"Mycodo {name}"
        self._unique_id = unique_id
        self._state = is_on

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        result = await self.hass.async_add_executor_job(
            self._client.set_switch_state, self._unique_id, True
        )
        if result and "Success" in result.get("message", ""):
            self._state = True
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to turn on {self._name}")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        result = await self.hass.async_add_executor_job(
            self._client.set_switch_state, self._unique_id, False
        )
        if result and "Success" in result.get("message", ""):
            self._state = False
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to turn off {self._name}")

    async def async_update(self):
        """Fetch new state data for the switch."""
        result = await self.hass.async_add_executor_job(
            self._client.get_switch_state, self._unique_id
        )
        if result:
            switch_state = result.get("output device channel states", [])
            self._state = switch_state.get("0", "off") == "on"
        else:
            _LOGGER.error(f"Failed to update {self._name}")
