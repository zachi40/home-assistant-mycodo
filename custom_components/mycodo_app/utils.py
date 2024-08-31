import asyncio
import atexit
import json
import logging
import random
from types import MappingProxyType
from typing import Optional, Any

import aiohttp
from aiohttp import ClientSession

from .const import CONF_API_KEY, CONF_BASE_URL

_LOGGER = logging.getLogger(__name__)


async def on_request_start_debug(session: aiohttp.ClientSession, context, params: aiohttp.TraceRequestStartParams):
    #if "192.168.1.195" in str(params.url):
    #    _LOGGER.debug(f"aiohttp {params.method}: {params.url}")
    pass


async def on_request_chunk_sent_debug(session: aiohttp.ClientSession, context,
                                      params: aiohttp.TraceRequestChunkSentParams):
    #if (params.method == "POST" or params.method == "PUT") and params.chunk:
    #    _LOGGER.debug(f"aiohttp Content {params.method}: {params.chunk}")
    pass


async def on_request_end_debug(session: aiohttp.ClientSession, context, params: aiohttp.TraceRequestEndParams):
    #if "192.168.1.195" in str(params.url):
    #    _LOGGER.debug(
    #        f"aiohttp url: {params.url} method: {params.method} Response <{params.response.status}>: {await params.response.text()}")
    pass


class MycodoClient:
    """Client to interact with the Mycodo API."""

    def __init__(self, entry_data: MappingProxyType[str, Any], session: Optional[ClientSession] = None):
        """Initialize the Mycodo client."""
        self.base_url = entry_data.get(CONF_BASE_URL)
        self.headers = {
            "accept": "application/vnd.mycodo.v1+json",
            "X-API-KEY": entry_data.get(CONF_API_KEY),
        }
        # Custom Logger to the session
        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_start.append(on_request_start_debug)
        trace_config.on_request_chunk_sent.append(on_request_chunk_sent_debug)
        trace_config.on_request_end.append(on_request_end_debug)
        trace_config.freeze()
        session.trace_configs.append(trace_config)

        if not session:
            session = aiohttp.ClientSession(trace_configs=[trace_config])
            atexit.register(self._shutdown)
        else:
            session.trace_configs.append(trace_config)

        self._session = session

    def _shutdown(self):
        if not self._session.closed:
            asyncio.run(self._session.close())

    async def make_request(self, endpoint, method="get", data={}, timeout: Optional[int] = 30):
        """Make an asynchronous HTTP request to a given Mycodo endpoint."""
        url = f"{self.base_url}/{endpoint}"
        resp_content = ""
        try:
            if not timeout:
                timeout = self._session.timeout
            if method == "get":
                resp = await self._session.get(url=url, headers=self.headers, timeout=timeout, ssl=False)
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'application/vnd.mycodo.v1+json' in content_type:
                    return await resp.json()
                else:
                    return await resp.text()
            elif method == "post":
                resp = await self._session.post(url=url, json= data, headers=self.headers, timeout=timeout, ssl=False)
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'application/vnd.mycodo.v1+json' in content_type:
                    return await resp.json()
                else:
                    return await resp.text()
            else:
                _LOGGER.error(f"Unsupported HTTP method: {method}")
                return None

        except aiohttp.ClientError as e:
            _LOGGER.error(f"ClientError: Exception when making HTTP request to {url}: {e}")
        except aiohttp.http_exceptions.HttpProcessingError as e:
            _LOGGER.error(f"HTTP processing error: {e.message}, Status: {e.status}")
        except Exception as e:
                _LOGGER.error(f"Unexpected error: {str(e)}")

        return resp_content or None

    async def get_sensors(self):
        """Get sensors from Mycodo."""
        _LOGGER.debug("Get sensors from Mycodo.")
        return await self.make_request("api/inputs")

    async def get_sensor_details(self, sensor_id):
        """Get detailed information for a specific sensor from Mycodo."""
        _LOGGER.debug(f"Get detailed information for {sensor_id} sensor from Mycodo.")
        return await self.make_request(f"api/inputs/{sensor_id}")

    async def get_sensor_data(self, sensor_device_id, unique_id):
        """Get the latest data for a specific sensor from Mycodo."""
        _LOGGER.debug(f"Get the latest data for a {sensor_device_id} sensor from Mycodo.")

        NOT_value = True
        count = 0
        while NOT_value:
            response = await self.make_request(f"last/{sensor_device_id}/input/{unique_id}/30")
            if count == 3:
                return None
            # 204 - no data
            elif response == "":
                await self.make_request(f"api/inputs/{sensor_device_id}/force-measurement", method="post")
                count += 1
            else:
                return json.loads(response)


    async def get_switches(self):
        """Get switches from Mycodo."""
        _LOGGER.debug("Get switches from Mycodo.")
        return await self.make_request("api/outputs")

    async def get_switch(self, switch_id):
        """Get the current state of a switch."""
        _LOGGER.debug(f"Get the current state of {switch_id}.")
        return await self.make_request(f"api/outputs/{switch_id}")


    async def set_switch_state(self, switch_id, channel, state):
        """Set the state of a switch."""
        return await self.make_request(
            endpoint=f"api/outputs/{switch_id}",
            method="post",
            data={"channel": channel, "state": state},
        )
