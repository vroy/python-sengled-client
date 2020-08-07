# Sengled Python Client

A simple Python client to control [Sengled](https://sengled.com) light and plug accessories.

There are other accessories but this was only tested with these three devices:

* A19 element color plus (E11-N1EA)
* A19 element classic (E11-G13)
* Smart plug (E1C-NB6)

## Installation

```
pip install sengled-client
```

## Usage

Create the API client:

```python
import sengled

api = sengled.api(
    # The username/password that you used to create your mobile account in
    # the Sengled Home app.
    username="your-username@example.com",
    password="your-secure-password",

    # Optional path to persist the session across multiple process
    # starts and reduce the number of logins.
    session_path="/tmp/sengled.pickle",

    # Prints details of the api request/responses when True, defaults to false.
    debug=True
)
```

Alternatively, set `SENGLED_*` environment variables that match the api arguments.

```python
import sengled

api = sengled.api_from_env()
```

List all devices

```python
devices = api.get_device_details()
```

List lamps that support colors

```python
colored = api.filter_colored_lamps()
```

List lamps that support color temperature

```python
temperature = api.filter_color_temperature_lamps()
```

The API can be used to modify a list of devices or single devices

```python
api.set_on(devices)

api.set_brightness(devices, 100)

api.set_color(colored, [255, 0, 0])

api.set_color_temperature(temperature, 100)

api.set_off(devices[0])

api.set_on_off(devices, True)
```

You can search for single devices

```python
api.find_by_id("B0CE18140000EB41") #=> SengledLampDevice

api.find_by_name("Office Bulb 1")  #=> SengledLampDevice
```

And finally you can operate directly on `SengledLampDevice`s

```python
bulb = api.find_by_name("Office Bulb 1")
bulb.on()
bulb.set_brightness(50)
bulb.set_color_temperature(50)
bulb.toggle()
```

Or chain the actions:

```python
api.find_by_name("Office Bulb 2") \
   .on() \
   .set_brightness(50) \
   .set_color([0, 0, 255])
```

Note that all API calls will raise based on status_code via request's
`raise_for_status()` method. Action methods will also raise a `RuntimeError`
if the `success` field is returned with a value of `False`.


## How this came about?

This was reverse engineered from multiple different repositories found on GitHub
as well as Charles.app and some guessing. See also:

* https://github.com/j796160836/homebridge-sengled/
* https://github.com/mpomery/sengled-element-postman/blob/master/Sengled%20Element%20API.postman_collection.json
* https://github.com/sroehl/sengled-python
* https://github.com/AHerridge/BetterSengled/blob/master/device.py
* https://github.com/NoxPhoenix/noxbot/blob/68281bac10aa6a939f617d1ba148944338566491/clients/sengledClient.js
