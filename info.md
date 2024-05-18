{% if prerelease %}
### NB!: This is a Beta version!
{% endif %}


# Mycodo App Integration

This integration allows you to connect and control your Mycodo App with Home Assistant.

## Features
- Monitor sensor data from Mycodo
- Control devices connected to Mycodo
- Automate tasks using Home Assistant automations

{% if not installed %}
## Installation

### Install with HACS (Recommended)
1. Add the URL to this repository as a custom integration in HACS.
2. Search for "Mycodo App Integration" and install it.
3. Restart Home Assistant.

### Manual Installation
1. Open the directory for your Home Assistant configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory there, create it.
3. In the `custom_components` directory, create a new folder called `mycodo_app`.
4. Download all the files from the `custom_components/mycodo_app/` directory in this repository.
5. Place the downloaded files in the newly created `mycodo_app` directory.
6. Restart Home Assistant.
7. In the Home Assistant UI, go to "Configuration" -> "Integrations" and click "+" to add a new integration.
8. Search for "Mycodo App" and follow the on-screen instructions.
{% endif %}
## Configuration
1. In Home Assistant, go to "Configuration" -> "Integrations".
2. Select "Mycodo App" and enter the following details:
   - **IP Address**: Enter the IP address of your Mycodo App.
   - **API Token**: Enter the API token you obtained earlier.
   - **App Name**: Enter a name for your Mycodo App.
   - **Protocol**: Select whether your app uses `HTTP` or `HTTPS` (default is `HTTPS`).

3. Complete the configuration by following the on-screen instructions.

For more detailed instructions, refer to the documentation in this repository.

## Support
If you encounter any issues or have questions, please open an issue in this repository or contact the maintainers.

---

Happy automating with Mycodo and Home Assistant!
