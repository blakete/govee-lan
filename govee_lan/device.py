"""Data classes representing Govee devices and their state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoveeDevice:
    """A Govee device discovered on the LAN."""
    ip: str
    device_id: str
    sku: str
    ble_version_hard: str = ""
    ble_version_soft: str = ""
    wifi_version_hard: str = ""
    wifi_version_soft: str = ""

    @classmethod
    def from_scan_response(cls, data: dict) -> GoveeDevice:
        return cls(
            ip=data.get("ip", ""),
            device_id=data.get("device", ""),
            sku=data.get("sku", ""),
            ble_version_hard=data.get("bleVersionHard", ""),
            ble_version_soft=data.get("bleVersionSoft", ""),
            wifi_version_hard=data.get("wifiVersionHard", ""),
            wifi_version_soft=data.get("wifiVersionSoft", ""),
        )


@dataclass(frozen=True)
class DeviceStatus:
    """Current state of a Govee device."""
    on: bool
    brightness: int
    color_r: int
    color_g: int
    color_b: int
    color_temp_kelvin: int

    @classmethod
    def from_status_response(cls, data: dict) -> DeviceStatus:
        color = data.get("color", {})
        return cls(
            on=data.get("onOff") == 1,
            brightness=data.get("brightness", 0),
            color_r=color.get("r", 0),
            color_g=color.get("g", 0),
            color_b=color.get("b", 0),
            color_temp_kelvin=data.get("colorTemInKelvin", 0),
        )
