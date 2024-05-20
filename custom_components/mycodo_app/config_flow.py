import logging
import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_NAME, CONF_IP_ADDRESS, CONF_API_KEY, CONF_USE_HTTPS

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_USE_HTTPS, default=True): cv.boolean,
    }
)


class MycodoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._ip_address = None
        self.name = None
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        self._errors = {}
        _LOGGER.info("Initializing the user step in the configuration flow")

        if user_input is not None:
            protocol = "https" if user_input[CONF_USE_HTTPS] else "http"
            _LOGGER.info(f"Protocol selected: {protocol}")

            # Validate IP
            if not await self._check_ip_live(user_input[CONF_IP_ADDRESS], protocol):
                self._errors["base"] = "ip_not_reachable"
                _LOGGER.error("IP address not reachable")

            # Validate API Key
            if not self._errors and not await self._check_api_key(
                user_input[CONF_IP_ADDRESS], user_input[CONF_API_KEY], protocol
            ):
                self._errors["base"] = "invalid_api_key"
                _LOGGER.error("API Key validation failed")

            if not self._errors:
                # Everything is valid, create the entry
                _LOGGER.info("Validation successful, creating entry")
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                _LOGGER.error(f"Errors in user input: {self._errors}")

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        _LOGGER.info("Showing configuration form")

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, "")): str,
                    vol.Required(
                        CONF_IP_ADDRESS, default=user_input.get(CONF_IP_ADDRESS, "")
                    ): str,
                    vol.Required(
                        CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")
                    ): str,
                    vol.Required(
                        CONF_USE_HTTPS, default=user_input.get(CONF_USE_HTTPS, True)
                    ): bool,
                }
            ),
            errors=self._errors,
            description_placeholders={
                "name_description": "The name you want to give this Mycodo instance.",
                "ip_address_description": "The IP address where your Mycodo instance is running.",
                "api_key_description": "The API key to connect to your Mycodo instance.",
                "use_https_description": "Use HTTPS to connect to Mycodo (disable for HTTP).",
            },
        )

    async def _check_ip_live(self, ip, protocol):
        """Check if the IP address is reachable."""
        try:
            session = async_get_clientsession(self.hass)
            async with session.head(
                f"{protocol}://{ip}/", timeout=5, ssl=False
            ) as response:
                _LOGGER.info(
                    f"Checking IP live: {protocol}://{ip} - Status code: {response.status}"
                )
                return response.status in (200, 302)
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error checking IP: {e}")
            return False

    async def _check_api_key(self, ip, api_key, protocol):
        """Validate the API key."""
        http_headers = {
            "accept": "application/vnd.mycodo.v1+json",
            "X-API-KEY": api_key,
        }

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                f"{protocol}://{ip}/api/settings/users",
                headers=http_headers,
                timeout=10,
                ssl=False,
            ) as response:
                _LOGGER.info(
                    f"Checking API Key: {protocol}://{ip}/api/settings/users - Status code: {response.status}"
                )
                return response.status in (200, 302)
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error checking API Key: {e}")
            return False
