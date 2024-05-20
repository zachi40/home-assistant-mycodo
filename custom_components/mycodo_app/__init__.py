from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, CONF_IP_ADDRESS, CONF_API_KEY, CONF_USE_HTTPS
from .utils import MycodoClient


async def async_setup(hass: HomeAssistantType, config: dict):
    """Set up the Mycodo component."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Mycodo from a config entry."""
    # Get the config entry data
    # ip = entry.data[CONF_IP_ADDRESS]
    # api_key = entry.data[CONF_API_KEY]
    # used_https = entry.data[CONF_USE_HTTPS]
    # protocol = "https" if used_https else "http"
    # base_url = f"{protocol}://{ip}/"

    # # Create a Mycodo client and save it in hass.data
    # hass.data[DOMAIN]["client"] = MycodoClient(base_url=base_url, api_key=api_key)
    hass.data[DOMAIN]["client"] = MycodoClient(
        base_url=f"{'https' if entry.data[CONF_USE_HTTPS] else 'http'}://{entry.data[CONF_IP_ADDRESS]}",
        api_key=entry.data[CONF_API_KEY],
    )

    async def update_mycodo_entities(_):
        """Update sensors and switches from Mycodo."""
        await hass.config_entries.async_forward_entry_unload(entry, "sensor")
        await hass.config_entries.async_forward_entry_unload(entry, "switch")
        await hass.config_entries.async_forward_entry_setup(entry, "sensor")
        await hass.config_entries.async_forward_entry_setup(entry, "switch")

    async_track_time_interval(hass, update_mycodo_entities, timedelta(minutes=20))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True
