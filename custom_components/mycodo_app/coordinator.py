import asyncio
import logging
import socket
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .utils import MycodoClient
from .const import DOMAIN, CONF_UPDATE_INTERVAL
_LOGGER = logging.getLogger(__name__)


class MycodoApiCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Initialize the coordinator."""
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self._config_entry = config_entry
        self._entry_data = config_entry.data
        update_interval = int(self._entry_data.get(CONF_UPDATE_INTERVAL, 5))
        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=timedelta(minutes=update_interval),  # Adjust the update interval as needed
                         )

        self._client = MycodoClient(entry_data=self._entry_data,
                                    session=async_create_clientsession(hass, verify_ssl=False, family=socket.AF_INET)
                                    )

        @callback
        def _dummy_listener() -> None:
            pass

        # Force the coordinator to periodically update by registering at least one listener.
        # Needed when the _async_update_data below returns {} for utilities that don't provide
        # forecast, which results to no sensors added, no registered listeners, and thus
        # _async_update_data not periodically getting called which is needed for _insert_statistics.
        self.async_add_listener(_dummy_listener)

    async def _async_update_data(self):
        """
        Fetch data from the MyCodo API.

        This method is responsible for asynchronously fetching sensor and switch data
        from the MyCodo API. It organizes the fetched data into a dictionary
        with keys corresponding to the Home Assistant platform (e.g., SENSOR, SWITCH).

        Returns:
            dict: A dictionary containing sensor and switch data fetched from the API.
        """
        try:
            data = {Platform.SENSOR: await self._fetch_sensor_data(), Platform.SWITCH: await self._fetch_switch_data()}
            return data

        except (asyncio.TimeoutError, Exception) as err:
            _LOGGER.error("Failed to fetch data from MyCodo API: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with MyCodo API: {err}") from err


    async def _fetch_sensor_data(self):
        try:
            sensor_data = []
            sensors = await self._client.get_sensors()
            # Attempt to extract necessary measurement details
            for sensor in sensors.get("input settings", []):
                if sensor.get("is_activated"):
                    device_id = sensor.get("unique_id")
                    sensor_details = await self._client.get_sensor_details(device_id)
                    if not sensor_details:
                        _LOGGER.error(f"Failed to fetch details for sensor {sensor.get('name')} with ID {device_id}")
                        continue

                    # Attempt to extract necessary measurement details
                    for device in sensor_details["device measurements"]:
                        # device_measurements = details["device measurements"][0]
                        unit = device.get("unit", "")
                        device_class = device.get("measurement", "")
                        channel = device.get("channel", "")
                        unique_id = device["unique_id"]
                        name = sensor.get("name", "")
                        data = await self._client.get_sensor_data(device.get("device_id"),
                                                                  device.get("unique_id")
                                                                  )
                        state = None
                        if data:
                            state = data[1]
                            if state is not None:
                                state = "{:.2f}".format(float(state))
                        else:
                            state = ""
                            _LOGGER.error(
                                f"Failed to update sensor ID {unique_id} sensor"
                            )
                        sensor_data.append({
                            "sensor_id": unique_id,
                            "sensor_data": {
                                "name": name,
                                "device_id": device_id,  # the main sensor uuid
                                "unique_id": unique_id,
                                "device_class": device_class,
                                "state": state,
                                "unit": unit,
                                "channel": channel
                            }
                        })
            _LOGGER.debug("Sensors fetched from MyCodo API is done")
            return sensor_data

        except Exception as err:
            _LOGGER.error("Error fetching sensor data, %s", err)

    async def _fetch_switch_data(self):
        switch_entities = []
        switches = await self._client.get_switches()

        if not switches or "output devices" not in switches:
            _LOGGER.error("Failed to fetch switches from Mycodo.")
            return

        for switch in switches.get("output devices", []):
            switch_options = await self._client.get_switch(switch["unique_id"])
            for output in switch_options.get("output device channels", []):
                channel = output.get("channel")
                output_id = output.get("output_id")
                unique_id = output.get("unique_id")
                name = f'{switch_options["output device"].get("name")} {output.get("name")}'
                state = switch_options["output device channel states"].get(str(channel))
                if state is None:
                    continue
                switch_entities.append({
                    "switch_id": unique_id,
                    "switch_data": {
                        "name": name,
                        "unique_id": unique_id,
                        "output_id": output_id,
                        "state": state == "on",
                        "channel": channel
                    }
                })
        _LOGGER.debug("switches fetched from MyCodo API is done")
        return switch_entities

