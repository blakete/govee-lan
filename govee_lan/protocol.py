"""Govee LAN API protocol constants and message builders."""

from __future__ import annotations

import json

MULTICAST_GROUP = "239.255.255.250"
BROADCAST_ADDR = "255.255.255.255"
DISCOVERY_PORT = 4001
LISTEN_PORT = 4002
CONTROL_PORT = 4003

DEFAULT_SCAN_TIMEOUT = 3.0
DEFAULT_CMD_TIMEOUT = 3.0


def build_scan() -> bytes:
    return _encode({"cmd": "scan", "data": {"account_topic": "reserve"}})


def build_turn(on: bool) -> bytes:
    return _encode({"cmd": "turn", "data": {"value": 1 if on else 0}})


def build_brightness(value: int) -> bytes:
    value = max(1, min(100, value))
    return _encode({"cmd": "brightness", "data": {"value": value}})


def build_color(r: int, g: int, b: int) -> bytes:
    r, g, b = (max(0, min(255, c)) for c in (r, g, b))
    return _encode(
        {
            "cmd": "colorwc",
            "data": {"color": {"r": r, "g": g, "b": b}, "colorTemInKelvin": 0},
        }
    )


def build_color_temp(kelvin: int) -> bytes:
    kelvin = max(2000, min(9000, kelvin))
    return _encode(
        {
            "cmd": "colorwc",
            "data": {"color": {"r": 0, "g": 0, "b": 0}, "colorTemInKelvin": kelvin},
        }
    )


def build_status_request() -> bytes:
    return _encode({"cmd": "devStatus", "data": {}})


def parse_message(data: bytes) -> dict:
    return json.loads(data.decode())


def _encode(msg_body: dict) -> bytes:
    return json.dumps({"msg": msg_body}).encode()
