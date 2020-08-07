import pickle
import time

import requests

class SengledSession():
    """
    Container holding the logged in session of the Sengled API for up to
    24 hours. This will help reduce the number of logins and speed up
    operations.

    This object is to be created with `SengledSession.load(persist_path)`,
    where persist_path is a path on disk where the session can be pickled.
    Set persist_path to None to skip pickling.
    """
    SESSION_TIMEOUT = 60 * 60 * 24

    def load(persist_path):
        if persist_path is None:
            return SengledSession(None)

        try:
            with open(persist_path, "rb") as f:
                return pickle.load(f)
        except:
            return SengledSession(persist_path)

    def __init__(self, persist_path):
        self.jar = requests.cookies.RequestsCookieJar()
        self.last_login = None

        self.persist_path = persist_path

    def logged_in(self, jar):
        self.jar = jar
        self.last_login = time.time()

        if self.persist_path:
            with open(self.persist_path, "wb") as f:
                pickle.dump(self, f)

    def is_valid(self):
        if self.last_login is None:
            return False

        if time.time() - self.last_login > SengledSession.SESSION_TIMEOUT:
            return False

        return True

class SengledLampDevice():
    """
    A wrapper around around the results of the `getDeviceDetails` API, with
    support for actions.

    {'deviceUuid': 'B0CE18140000EB41', 'deviceClass': 1, 'supportAttributes': '0,1,2,3,4,12,13', 'attributes': {'deviceRssi': '2', 'rgbColorR': '255', 'activeTime': '2020-03-23 13:11:26', 'colorMode': '1', 'rgbColorG': '255', 'isOnline': '1', 'version': '48', 'typeCode': 'E11-N1EA', 'colorTemperature': '0', 'productCode': 'E11-N1EA', 'brightness': '51', 'rgbColorB': '0', 'name': 'Office Bulb 2', 'onCount': '42', 'onoff': '1'}}
    """
    def __init__(self, api, data):
        self.api   =  api

        self.id           = data["deviceUuid"]
        self.name         = data["attributes"]["name"]
        self.product_code = data["attributes"]["typeCode"]
        self.version      = data["attributes"]["version"]

        self.is_online  = bool(int(data["attributes"]["isOnline"]))
        self.onoff      = bool(int(data["attributes"]["onoff"]))

        if "brightness" in data["attributes"]:
            self.brightness = int(data["attributes"]["brightness"])
        else:
            self.brightness = None

        if "colorTemperature" in data["attributes"]:
            self.color_temperature = int(data["attributes"]["colorTemperature"])
        else:
            # Not supported
            self.color_temperature = None

        if "rgbColorR" in data["attributes"]:
            self.color = [
                data["attributes"]["rgbColorR"],
                data["attributes"]["rgbColorG"],
                data["attributes"]["rgbColorB"],
            ]
        else:
            # Not supported
            self.color = None

    def toggle(self):
        self.set_on_off(not self.onoff)
        return self

    def on(self):
        self.set_on_off(True)
        return self

    def off(self):
        self.set_on_off(False)
        return self

    def set_on_off(self, onoff):
        self.onoff = bool(onoff)
        self.api.set_on_off([self], onoff)
        return self

    def set_brightness(self, brightness):
        self.api.set_brightness(self, brightness)
        return self

    def set_color_temperature(self, temperature):
        self.api.set_color_temperature(self, temperature)
        return self


    def set_color(self, color):
        self.color = color
        self.api.set_color(self, color)
        return self

    def __repr__(self):
        return (
            f"SengledLampDevice(\n"
            f"  id: {self.id}\n"
            f"  name: {self.name}\n"
            f"  product_code: {self.product_code}\n"
            f"  version: {self.version}\n"
            f"  is_online: {self.is_online}\n"
            f"  onoff: {self.onoff}\n"
            f"  brightness: {self.brightness}\n"
            f"  color_temperature: {self.color_temperature}\n"
            f"  color: {self.color}\n"
            f")"
        )

class SengledAPI():
    BASE_URL = "https://element.cloud.sengled.com/zigbee"

    def __init__(self, username, password, session_path=None, debug=False):
        self.username = username
        self.password = password
        self.debug    = debug

        self.session = SengledSession.load(session_path)
        self.login()

        self.devices = None

    def login(self):
        if self.session.is_valid():
            return

        response = self._post("customer/login.json", {
            "os_type": "android",
            "user": self.username,
            "pwd": self.password,
            "uuid": "xxxxxx"
        })

        self.session.logged_in(response.cookies)

    def get_device_details(self, refresh=False):
        """
        Get all lamp devices.

        This will be cached, use `refresh=True` to force the API call.
        """
        if self.devices is not None and not refresh:
            return self.devices

        response = self._post("device/getDeviceDetails.json")

        devices = []

        for gateway in response.json()["deviceInfos"]:
            devices += gateway.get("lampInfos", [])

        self.devices = [SengledLampDevice(self, device) for device in devices]

        return self.devices

    def find_by_id(self, id):
        """
        Find a single device by ID.

        Raises RuntimeError if a single device can't be found.
        """
        matches = [device for device in self.get_device_details() if device.id == id]

        if len(matches) > 1:
            raise RuntimeError(f"Found more than one device for id '{id}'")

        if len(matches) < 1:
            raise RuntimeError(f"Could not find a device for id '{id}'")

        return matches[0]

    def find_by_name(self, name):
        """
        Find a single device by name.

        Raises RuntimeError if a single device can't be found
        """
        matches = [device for device in self.get_device_details() if device.name == name]

        if len(matches) > 1:
            raise RuntimeError(f"Found more than one device for name '{name}'")

        if len(matches) < 1:
            raise RuntimeError(f"Could not find a device for name '{name}'")

        return matches[0]

    def filter_colored_lamps(self):
        """A list of lamps that support color adjustments"""
        return [d for d in self.get_device_details() if d.color is not None]

    def filter_color_temperature_lamps(self):
        """A list of lamps that support color temperature adjustments"""
        return [d for d in self.get_device_details() if d.color_temperature is not None]

    def set_on(self, devices):
        """Turn on devices"""
        self.set_on_off(devices, True)

    def set_off(self, devices):
        """Turn off devices"""
        self.set_on_off(devices, False)

    def set_on_off(self, devices, onoff):
        """
        Toggle the on/off status of multiple devices.
        onoff: 0 or 1
        """
        self._device_set_group(128, devices, { "value": int(onoff) })

    def set_brightness(self, devices, brightness_percentage):
        """
        Set the brightness of a light device.

        brightness: 0 - 100
        """
        if brightness_percentage < 0 or brightness_percentage > 100:
            raise ArgumentError("brightness percentage should be a value between 0 and 100")

        brightness = round((brightness_percentage / 100) * 255)

        self._device_set_group(127, devices, { "value": brightness })

    def set_color_temperature(self, devices, temperature):
        """
        Set the color temperature of a light device.

        temperature: 0 (warm) - 100 (cold)
        """
        if temperature < 0 or temperature > 100:
            raise ArgumentError("color temperature should be a value between 0 and 100")

        self._device_set_group(126, devices, { "value": temperature })

    def set_color(self, devices, color):
        """
        Set the color of a light device.

        device_id: A single device ID or a list to update multiple at once
        color: [red(0-255), green(0-255), blue(0-255)]
        """
        self._device_set_group(129, devices, {
            "rgbColorR": color[0],
            "rgbColorG": color[1],
            "rgbColorB": color[2],
        })

    def _device_set_group(self, cmd_id, devices, data):
        params = {
            "cmdId": cmd_id,
            "deviceUuidList": self._normalize_devices(devices),
        }

        for key, value in data.items():
            params[key] = value

        response = self._post("device/deviceSetGroup.json", params)

        if "success" in response.json() and not response.json()["success"]:
            raise RuntimeError("This operation did not succeed: {response.json()}")

    def _normalize_devices(self, devices):
        if not isinstance(devices, list):
            devices = [devices]

        device_ids = [
            device.id if isinstance(device, SengledLampDevice) else device
            for device in devices
        ]

        for id in device_ids:
            if not isinstance(id, str):
                raise ArgumentError(f"Received invalid device ID: {id}")

        return device_ids


    def _post(self, path, data={}):
        if self.debug:
            print(f"request: {path}, {data}")

        response = requests.post(
            f"{self.BASE_URL}/{path}",
            cookies=self.session.jar,
            json=data
        )
        response.raise_for_status()

        if self.debug:
            print(f"response: {response.json()}")
        return response
