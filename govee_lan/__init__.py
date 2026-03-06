"""Discover and control Govee lights over the local network via the Govee LAN API."""

from govee_lan.device import GoveeDevice, DeviceStatus
from govee_lan.scanner import scan
from govee_lan.controller import turn_on, turn_off, set_brightness, set_color, set_color_temp, get_status

__all__ = [
    "GoveeDevice",
    "DeviceStatus",
    "scan",
    "turn_on",
    "turn_off",
    "set_brightness",
    "set_color",
    "set_color_temp",
    "get_status",
]
