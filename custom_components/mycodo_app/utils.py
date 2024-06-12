import requests
import logging

_LOGGER = logging.getLogger(__name__)
# Disable SSL warnings (for self-signed certificates)
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class MycodoClient:
    """Client to interact with the Mycodo API."""

    def __init__(self, base_url, api_key):
        """Initialize the Mycodo client."""
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "accept": "application/vnd.mycodo.v1+json",
            "X-API-KEY": api_key,
        }

    def make_request(self, endpoint, method="get", data=None):
        """Make a HTTP request to a given Mycodo endpoint."""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "get":
                response = requests.get(url, headers=self.headers, verify=False)
            elif method == "post":
                response = requests.post(
                    url, json=data, headers=self.headers, verify=False
                )
            else:
                _LOGGER.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code == 200:
                return response.json()
            else:
                _LOGGER.error(
                    f"HTTP request to {url} failed with status {response.status_code}: {response.text}"
                )
                return None
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Exception when making HTTP request to {url}: {e}")
            return None

    def get_sensors(self):
        """Get sensors from Mycodo."""
        return self.make_request("api/inputs")

    def get_sensor_details(self, sensor_id):
        """Get detailed information for a specific sensor from Mycodo."""
        return self.make_request(f"api/inputs/{sensor_id}")

    def get_sensor_data(self, sensor_id):
        """Get the latest data for a specific sensor from Mycodo."""
        NOT_value = True
        respose = self.make_request(f"api/measurements/last/{sensor_id}/C/0/30")
        while NOT_value:
            if not respose.get("value"):
                random_number = random.randint(10, 60)
                respose = self.make_request(
                    f"api/measurements/last/{sensor_id}/C/0/{random_number}"
                )
            else:
                return respose

    def get_switches(self):
        """Get switches from Mycodo."""
        return self.make_request("api/outputs")

    def get_switch_state(self, switch_id):
        """Get the current state of a switch."""
        return self.make_request(f"api/outputs/{switch_id}")

    def set_switch_state(self, switch_id, state):
        """Set the state of a switch."""
        return self.make_request(
            endpoint=f"api/outputs/{switch_id}",
            method="post",
            data={"channel": 0, "state": state},
        )
