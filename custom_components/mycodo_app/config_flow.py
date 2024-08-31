import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import selector
from .const import DOMAIN, CONF_NAME, CONF_IP_ADDRESS, CONF_API_KEY, CONF_USE_HTTPS, CONF_BASE_URL, CONF_UPDATE_INTERVAL

_LOGGER: logging.Logger = logging.getLogger(__package__)

# Configuration schema
CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required(CONF_API_KEY): str,
    vol.Optional(CONF_USE_HTTPS, default=True): bool,
    vol.Optional(CONF_UPDATE_INTERVAL, default=30):
        selector({"number": {"min": 1, "max": 60, "unit_of_measurement": "minutes", "mode": "slider", "step": 1}})
})


class MycodoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.protocol = None
        self.name = None
        self._errors = {}
        self.session = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initiated by the user."""
        self._errors: dict[str, str] = {}
        _LOGGER.debug("Initializing the user step in the configuration flow")

        if user_input is not None:
            self._session = async_get_clientsession(self.hass)
            protocol = "https" if user_input[CONF_USE_HTTPS] else "http"
            self.protocol = protocol
            _LOGGER.debug(f"Protocol selected: {self.protocol}")

            # Validate IP
            if not await self._check_ip_live(user_input):
                self._errors["base"] = "ip_not_reachable"
                _LOGGER.error("IP address not reachable")

            # Validate API Key
            if not self._errors and not await self._check_api_key(user_input):
                self._errors["base"] = "invalid_api_key"
                _LOGGER.error("API Key validation failed")

            if not self._errors:
                await self._get_hostname(user_input)
                base_url = f"{protocol}://{user_input.get(CONF_IP_ADDRESS)}"
                user_input.update({CONF_NAME: self.name, CONF_BASE_URL: base_url})
                # Everything is valid, create the entry
                _LOGGER.debug("Validation successful, creating entry")
                return self.async_create_entry(title=f"{user_input[CONF_NAME]}-mycodo", data=user_input)
            else:
                _LOGGER.error(f"Errors in user input: {self._errors}")

                return self.async_show_form(step_id="user",
                                            data_schema=
                                            vol.Schema({
                                                vol.Required(CONF_IP_ADDRESS,
                                                             default=user_input.get(CONF_IP_ADDRESS, "")): str,
                                                vol.Required(CONF_API_KEY,
                                                             default=user_input.get(CONF_API_KEY, "")): str,
                                                vol.Optional(CONF_USE_HTTPS,
                                                             default=user_input.get(CONF_USE_HTTPS, True)): bool,
                                                vol.Optional(CONF_UPDATE_INTERVAL,
                                                             default=user_input.get(CONF_UPDATE_INTERVAL)):
                                                # selector({"number": {"min": 60,"max": 3600,"unit_of_measurement": "seconds","mode": "slider","step": 1,}
                                                    selector({"number": {"min": 1, "max": 60,
                                                                         "unit_of_measurement": "minutes",
                                                                         "mode": "slider", "step": 1, }
                                                              })
                                            }),
                                            errors=self._errors,
                                            )
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, errors=self._errors)

    async def _check_ip_live(self, user_input: dict[str, Any]):
        """Check if the IP address is reachable."""
        url = f"{self.protocol}://{user_input.get('ip_address')}/"
        try:
            response = await self._session.head(url=url, timeout=10, ssl=False)
            _LOGGER.debug(f"Checking IP live- got status code: {response.status}")
            return response.status in (200, 302)

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error checking IP: {e}")
            return False

    async def _check_api_key(self, user_input: dict[str, Any]):
        """Validate the API key."""
        url = f"{self.protocol}://{user_input.get('ip_address')}/api/settings/users"
        http_headers = {"accept": "application/vnd.mycodo.v1+json", "X-API-KEY": user_input.get('api_key'), }

        try:
            response = await self._session.get(url=url, headers=http_headers, timeout=10, ssl=False)
            _LOGGER.debug(f"Checking API Key - got status code: {response.status}")
            return response.status in (200, 302)

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error checking API Key: {e}")
            return False

    async def _get_hostname(self, user_input: dict[str, Any]) -> None:
        """get the mycodo device hostname."""
        url = f"{self.protocol}://{user_input.get('ip_address')}/"

        try:
            response = await self._session.get(url=url, timeout=10, ssl=False)
            response_html = await response.text()
            _LOGGER.debug(f"Checking Hostname - got status code: {response.status}")
            # Regex to find the page title
            title_match = re.search(r'<title>(.*?)</title>', response_html, re.IGNORECASE)

            if title_match:
                title = title_match.group(1)
                # Extract the string before the hyphen
                specific_match = re.search(r'^(.*?)\s*-\s*', title)
                if specific_match:
                    hostname = specific_match.group(1).strip()
                    _LOGGER.debug(f"mycodo Hostname is: {hostname}")
                    self.name = hostname
                else:
                    self.name = "mycodo"
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error checking API Key: {e}")
            return False
