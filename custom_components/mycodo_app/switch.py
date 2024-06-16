import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Mycodo switches."""
    mycodo_client = hass.data[DOMAIN]["client"]
    switches = await hass.async_add_executor_job(mycodo_client.get_switches)

    if not switches or "output devices" not in switches:
        _LOGGER.error("Failed to fetch switches from Mycodo.")
        return

    switch_entities = []
    output_devices = switches.get("output devices", [])
    for switch in output_devices:
        # get all channel from switch
        switch_options = await hass.async_add_executor_job(
            mycodo_client.get_switch, switch["unique_id"]
        )
        for output in switch_options.get("output device channels", []):
            channel = output.get("channel")
            output_id = output.get("output_id")
            unique_id = output.get("unique_id")
            name = f'{switch_options["output device"].get("name")} {output.get("name")}'
            state = switch_options["output device channel states"].get(str(channel))
            if state is None:
                continue
            switch_entities.append(
                MycodoSwitch(
                    mycodo_client,
                    name,
                    unique_id,
                    output_id,
                    channel,
                    state == "on",
                )
            )

    async_add_entities(switch_entities)


class MycodoSwitch(SwitchEntity):
    """Representation of a Mycodo Switch."""

    def __init__(self, mycodo_client, name, unique_id, output_id, channel, is_on):
        """Initialize the switch."""
        self._client = mycodo_client
        self._name = f"Mycodo {name}"
        self._unique_id = unique_id
        self._output_id = output_id
        self._channel = channel
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
    def output_id(self):
        """Return the output ID of the switch."""
        return self._output_id

    @property
    def channel(self):
        """Return the channel of the switch."""
        return self._channel

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        result = await self.hass.async_add_executor_job(
            self._client.set_switch_state, self._output_id, self._channel, True
        )
        if result and "Success" in result.get("message", ""):
            self._state = True
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to turn on {self._name}")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        result = await self.hass.async_add_executor_job(
            self._client.set_switch_state, self._output_id, self._channel, False
        )
        if result and "Success" in result.get("message", ""):
            self._state = False
            self.async_write_ha_state()
        else:
            _LOGGER.error(f"Failed to turn off {self._name}")

    async def async_update(self):
        """Fetch new state data for the switch."""
        result = await self.hass.async_add_executor_job(
            self._client.get_switch, self._output_id
        )
        if result:
            switch_state = result.get("output device channel states", [])
            self._state = switch_state.get(str(self._channel), "off") == "on"
        else:
            _LOGGER.error(f"Failed to update {self._name}")
