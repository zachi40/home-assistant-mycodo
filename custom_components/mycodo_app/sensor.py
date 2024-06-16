import logging
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT, TEMP_KELVIN

# str(UnitOfTemperature.CELSIUS)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Mycodo sensors dynamically from a config entry."""
    mycodo_client = hass.data[DOMAIN]["client"]

    # Fetch basic sensors data
    sensors = await hass.async_add_executor_job(mycodo_client.get_sensors)

    if not sensors or "input settings" not in sensors:
        _LOGGER.error("Failed to fetch sensors from Mycodo.")
        return

    sensor_entities = []
    input_settings = sensors.get("input settings", []) or []
    for sensor in input_settings:
        if sensor.get("is_activated"):
            # Fetch detailed sensor information
            details = await hass.async_add_executor_job(
                mycodo_client.get_sensor_details, sensor["unique_id"]
            )
            if not details:
                _LOGGER.error(
                    f"Failed to fetch details for sensor {sensor['name']} with ID {sensor['unique_id']}"
                )
                continue

            try:
                # Attempt to extract necessary measurement details
                for device in details["device measurements"]:
                    # device_measurements = details["device measurements"][0]
                    unit = device.get("unit", "")
                    device_class = device.get("measurement", "")

                    channel = device.get("channel", "")

                    data = await hass.async_add_executor_job(
                        mycodo_client.get_sensor_data,
                        device.get("device_id"),
                        device.get("unique_id"),
                    )
                    if data:
                        state = data[1]
                        if state is not None:
                            state = "{:.2f}".format(float(state))
                    else:
                        _LOGGER.error(
                            f"Failed to update sensor ID {sensor["unique_id"]} sensor"
                        )

                    sensor_entities.append(
                        MycodoSensor(
                            mycodo_client,
                            sensor["name"],
                            device.get("unique_id"),
                            unit,
                            device_class,
                            channel,
                            device.get("device_id"),
                            state,
                        )
                    )
            except (IndexError, KeyError, TypeError) as e:
                _LOGGER.error(f"Error processing sensor {sensor['name']} details: {e}")
                continue

    async_add_entities(sensor_entities)


class MycodoSensor(Entity):
    """Representation of a Sensor from Mycodo."""

    def __init__(
        self,
        mycodo_client,
        name,
        unique_id,
        unit_of_measurement,
        device_class,
        channel,
        device_id,
        state,
    ):
        """Initialize the sensor."""
        self.mycodo_client = mycodo_client
        self._name = f"Mycodo {name} {device_class}"
        self._unique_id = unique_id
        self._unit_of_measurement = unit_of_measurement
        self._unit = unit_of_measurement
        self._channel = channel
        self._device_class = device_class
        self._device_id = device_id
        self._state = state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        unit = self._unit_of_measurement
        if unit == "C":
            return TEMP_CELSIUS
        elif unit == "F":
            return TEMP_FAHRENHEIT
        elif unit == "K":
            return TEMP_KELVIN
        elif unit == "percent":
            return "%"
        elif unit == "m_s":
            return "m/s"
        else:
            return unit

    @property
    def unit(self):
        """Return the unit of the sensor."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def channel(self):
        """Return the device channel of the sensor."""
        return self._channel

    @property
    def channel(self):
        """Return the device_id of the sensor."""
        return self._device_id

    async def async_update(self):
        """Fetch new state data for the sensor."""
        data = await self.hass.async_add_executor_job(
            self.mycodo_client.get_sensor_data, self._device_id, self._unique_id
        )
        if data:
            self._state = data[1]
            if self._state is not None:
                self._state = "{:.2f}".format(float(self._state))
            else:
                _LOGGER.error(
                    f"No data found for sensor '{self._name}' with ID {self._unique_id}"
                )
        else:
            _LOGGER.error(
                f"Failed to update sensor '{self._name}' with ID {self._unique_id}"
            )
