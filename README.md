# govee-lan

A simple Python library and CLI for discovering and controlling Govee lights over the local network using the [Govee LAN API](https://app-h5.govee.com/user-manual/wlan-guide).

No cloud account or API keys required -- all communication happens via UDP on your LAN.

## Prerequisites

- Python 3.11+
- Govee devices with LAN API enabled (Govee Home app → Device Settings → enable **LAN Control**)

## Install

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## CLI Usage

```bash
# Discover devices on the network
govee scan

# Power control
govee on 192.168.1.100
govee off 192.168.1.100

# Brightness (1-100)
govee brightness 192.168.1.100 75

# RGB color
govee color 192.168.1.100 255 0 128

# Color temperature (2000-9000K)
govee colortemp 192.168.1.100 6500

# Query device status
govee status 192.168.1.100
```

## Library Usage

```python
import govee_lan

# Discover devices
devices = govee_lan.scan()
for device in devices:
    print(f"{device.sku} at {device.ip}")

# Control a device
govee_lan.turn_on("192.168.1.100")
govee_lan.set_brightness("192.168.1.100", 80)
govee_lan.set_color("192.168.1.100", 255, 0, 128)
govee_lan.set_color_temp("192.168.1.100", 4000)

# Query status
status = govee_lan.get_status("192.168.1.100")
if status:
    print(f"On: {status.on}, Brightness: {status.brightness}%")
    print(f"Color: R={status.color_r} G={status.color_g} B={status.color_b}")
    print(f"Color Temp: {status.color_temp_kelvin}K")

govee_lan.turn_off("192.168.1.100")
```

## How It Works

Govee devices with LAN API enabled communicate via UDP:

| Port | Direction | Purpose |
|------|-----------|---------|
| 4001 | Client → Device | Discovery (multicast `239.255.255.250`) |
| 4002 | Device → Client | Responses |
| 4003 | Client → Device | Control commands |

## Running Tests

```bash
# Unit tests (no network required)
pytest

# Integration tests (requires Govee devices on your LAN)
# First create tests_integration/local_config.json:
#   {"device_ips": ["192.168.x.x"]}
pytest tests_integration/ -v -s
```

## License

MIT
