"""Discover and control Govee lights over the local network via the Govee LAN API."""

from govee_lan.controller import (
    get_status,
    list_scenes,
    set_brightness,
    set_color,
    set_color_temp,
    set_scene,
    set_scene_sync,
    turn_off,
    turn_on,
    turn_on_verified,
)
from govee_lan.device import DeviceStatus, GoveeDevice
from govee_lan.scanner import scan
from govee_lan.scenes import SceneInfo

__all__ = [
    "GoveeDevice",
    "DeviceStatus",
    "SceneInfo",
    "scan",
    "turn_on",
    "turn_on_verified",
    "turn_off",
    "set_brightness",
    "set_color",
    "set_color_temp",
    "get_status",
    "set_scene",
    "set_scene_sync",
    "list_scenes",
]
