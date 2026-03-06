"""Discover and control Govee lights over the local network via the Govee LAN API."""

from govee_lan.controller import get_status, set_brightness, set_color, set_color_temp, turn_off, turn_on
from govee_lan.device import DeviceStatus, GoveeDevice
from govee_lan.scanner import scan

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
