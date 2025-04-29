# Mycodo App Home Assistant Integration

### ⚠️ Known Issue in Version 8.16.1

> **Important:** There is a known bug in version `8.16.1` that prevents the system from retrieving information about existing inputs. **Do not upgrade to this version** if your system is already working correctly.

#### ✅ Temporary Fix

If you've already upgraded and are experiencing this issue, follow the steps below to resolve it:

1. Navigate to the Mycodo installation directory (default path: `/opt/Mycodo/`).
2. Open the `mycodo_flask` folder (default path: `/opt/Mycodo/mycodo/mycodo_flask/`).
3. Locate the `input.py` file inside the `API` subdirectory.
4. Modify line 11 from:
    ```python
    from mycodo.databases.models import DeviceMeasurements
    ```
    to:
    ```python
    from mycodo.databases.models.measurement import DeviceMeasurements
    ```

This will resolve the issue with input detection in version 8.16.1.


## Overview
This integration allows you to connect and control your Mycodo App with Home Assistant.

## Installation

### Install with HACS (Recommended)
1. Add the URL to this repository as a custom integration in HACS.
2. Search for "Mycodo App Integration" and install it.
3. Restart Home Assistant.

### Manual Installation
1. Open the directory for your Home Assistant configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory there, create it.
3. In the `custom_components` directory, create a new folder called `mycodo`.
4. Download all the files from the `custom_components/mycodo/` directory in this repository.
5. Place the downloaded files in the newly created `mycodo` directory.
6. Restart Home Assistant.
7. In the Home Assistant UI, go to "Configuration" -> "Integrations" and click "+" to add a new integration.
8. Search for "Mycodo App" and follow the on-screen instructions.

## Obtaining the Token
To integrate your Mycodo App with Home Assistant, you need an API token. Follow these steps to obtain the token:

1. Log in to your Mycodo App.
2. Click on the "Settings" button.
3. Navigate to "Configure".
4. Go to "Users" in the side menu.
5. In the "Users" section, click on the "Generate API Key" button.
6. Copy the generated token and keep it secure.

<img
  src='images/get_token.png'
  width='1000pt'
/>

Once you have the token, you can configure the integration in Home Assistant by providing the token during the setup process.

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
If you encounter any issues or have questions, please open an issue in this repository.

---
