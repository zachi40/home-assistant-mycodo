import logging
import uuid
from datetime import timedelta
from enum import Enum

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import MycodoApiCoordinator
from .mycodo_entity import mycodoEntity

_LOGGER = logging.getLogger(__name__)

class CustomSensorDeviceClass(Enum):
    """Custom enum that combines standard and custom sensor device classes."""
    # Include all standard SensorDeviceClass members
    TEMPERATURE = SensorDeviceClass.TEMPERATURE.value
    HUMIDITY = SensorDeviceClass.HUMIDITY.value
    PRESSURE = SensorDeviceClass.PRESSURE.value

    # Add custom device classes
    DEWPOINT = "dewpoint"
    DIRECTION = "direction"
    VAPOR_PRESSURE_DEFICIT = "vapor_pressure_deficit"

    # Add more custom classes as needed

    @classmethod
    def from_string(cls, name: str):
        """Get the enum member corresponding to a string, including standard and custom."""
        # Attempt to get the member from the custom enum
        try:
            return cls[name.upper()]
        except KeyError:
            # If not found in custom, check the standard SensorDeviceClass
            if name.upper() in SensorDeviceClass.__members__:
                return SensorDeviceClass[name.upper()]
            _LOGGER.debug(f"'{name}' is not a valid device class")
            return name


UNIT_MAP = {
    "C": UnitOfTemperature.CELSIUS,
    "F": UnitOfTemperature.FAHRENHEIT,
    "K": UnitOfTemperature.KELVIN,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Mycodo sensors dynamically from a config entry."""
    coordinator: MycodoApiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for sensor_dict in coordinator.data.get(Platform.SENSOR, []):
        # Assuming each dict contains a single sensor_id -> sensor_data pair
        sensor_id = sensor_dict.get("sensor_id")
        sensor_data = sensor_dict.get("sensor_data")

        if sensor_id and isinstance(sensor_data, dict):
            entities.append(MycodoSensor(coordinator, sensor_id, sensor_data))

    async_add_entities(entities, True)


class MycodoSensor(mycodoEntity, SensorEntity):
    def __init__(self, coordinator: MycodoApiCoordinator, sensor_id: str, sensor_data: dict):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator

        device_class_str = sensor_data.get("device_class", "temperature")
        self._device_class = CustomSensorDeviceClass.from_string(device_class_str)
        self._unit_of_measurement = sensor_data.get("unit", "")
        self._name = f"Mycodo_{sensor_data.get("name", "sensor")} {device_class_str}"
        self._sensor_id = sensor_id
        self._state = None
        self._unique_id = sensor_data.get("unique_id", str(uuid.uuid4()))
        self._channel = sensor_data.get("channel")
        self._device_id = sensor_data.get("device_id")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor, if any."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        return False

    @property
    def icon(self):
        mapping = {
            'C': "mdi:temperature-celsius",
            'F': "mdi:temperature-fahrenheit",
            'K': "mdi:temperature-kelvin",
            'Pa': "mdi:car-brake-low-pressure",
            'm_s': "mdi:speedometer",
            'percent': "mdi:percent",
            "bearing": "mdi:cog"
        }
        return mapping.get(self.unit_of_measurement, "mdi:eye")

    async def async_update(self):
        """Update the sensor data."""
        await self._coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        latest_data = next((sensor for sensor in self._coordinator.data.get(Platform.SENSOR, []) if
                            sensor.get('sensor_id') == self._sensor_id), None)
        if latest_data:
            self._state = latest_data.get('sensor_data', "").get('state', 0.0)
            _LOGGER.debug(f"Updated sensor {self._sensor_id} state to {self._state}")
        self.async_write_ha_state()
