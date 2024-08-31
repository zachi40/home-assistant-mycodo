import logging
import uuid

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import MycodoApiCoordinator
from .mycodo_entity import mycodoEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Mycodo switches."""

    coordinator: MycodoApiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []
    for switch_dict in coordinator.data.get(Platform.SWITCH, {}):
        switch_id = switch_dict.get("switch_id")
        switch_data = switch_dict.get("switch_data")

        if switch_id and isinstance(switch_data, dict):
            entities.append(MycodoSwitch(coordinator, switch_id, switch_data))
    async_add_entities(entities)


class MycodoSwitch(mycodoEntity, SwitchEntity):
    def __init__(self, coordinator, switch_id, switch_data):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._client = self._coordinator._client
        self._switch_id = switch_id

        self._name = f'mycodo_{switch_data.get("name", "mycodo_Switch")}'
        self._state = None
        self._unique_id = switch_data.get("unique_id", str(uuid.uuid4()))
        self._output_id = switch_data.get("output_id", str(uuid.uuid4()))
        self._channel = switch_data.get("channel", 0)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return True if the switch is on."""
        return self._state

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return self._unique_id

    async def async_turn_off(self):
        """Turn the switch on using the Mycodo API client."""
        try:
            self._state = False
            await self._coordinator._client.set_switch_state(self._output_id, self._channel, self._state)
            self.async_write_ha_state()  # Update Home Assistant state
            _LOGGER.debug(f"Turned on switch {self._unique_id}")
        except Exception as e:
            _LOGGER.error(f"Failed to turn on switch {self._unique_id}: {e}")

    async def async_turn_on(self):
        """Turn the switch off using the Mycodo API client."""
        try:
            self._state = True
            await self._coordinator._client.set_switch_state(self._output_id, self._channel, self._state)
            self.async_write_ha_state()  # Update Home Assistant state
            _LOGGER.debug(f"Turned off switch {self._unique_id}")
        except Exception as e:
            _LOGGER.error(f"Failed to turn off switch {self._unique_id}: {e}")

    async def async_update(self):
        """Update the switch data."""
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        latest_data = next((switch for switch in self._coordinator.data.get(Platform.SWITCH, []) if
                            switch.get('switch_id') == self._unique_id), None)
        if latest_data:
            self._state =latest_data.get('switch_data', "").get('state', False)
            _LOGGER.debug(f"Updated switch {self._output_id} state to {self._state}")
            self.async_write_ha_state()
