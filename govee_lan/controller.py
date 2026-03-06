"""Send control commands to Govee devices on the LAN."""

from __future__ import annotations

from govee_lan.device import DeviceStatus
from govee_lan.protocol import (
    CONTROL_PORT,
    DEFAULT_CMD_TIMEOUT,
    build_brightness,
    build_color,
    build_color_temp,
    build_status_request,
    build_turn,
)
from govee_lan.transport import make_listener, make_sender, recv_responses


def _send(ip: str, payload: bytes, expect_cmd: str | None = None, timeout: float = DEFAULT_CMD_TIMEOUT) -> dict | None:
    """Send a UDP payload to a device and optionally wait for a matching response."""
    listener = None
    if expect_cmd:
        listener = make_listener()

    sender = make_sender()
    sender.sendto(payload, (ip, CONTROL_PORT))
    sender.close()

    result = None
    if listener:
        for msg, _ in recv_responses(listener, timeout):
            try:
                if msg["msg"]["cmd"] == expect_cmd:
                    result = msg
                    break
            except (KeyError, TypeError):
                continue
        listener.close()
    return result


def turn_on(ip: str) -> None:
    """Turn a Govee device on."""
    _send(ip, build_turn(on=True))


def turn_off(ip: str) -> None:
    """Turn a Govee device off."""
    _send(ip, build_turn(on=False))


def set_brightness(ip: str, value: int) -> None:
    """Set brightness (1-100)."""
    _send(ip, build_brightness(value))


def set_color(ip: str, r: int, g: int, b: int) -> None:
    """Set an RGB color (each channel 0-255). Disables color temperature mode."""
    _send(ip, build_color(r, g, b))


def set_color_temp(ip: str, kelvin: int) -> None:
    """Set color temperature in Kelvin (2000-9000)."""
    _send(ip, build_color_temp(kelvin))


def get_status(ip: str, timeout: float = DEFAULT_CMD_TIMEOUT) -> DeviceStatus | None:
    """Query the current state of a device. Returns None on timeout."""
    result = _send(ip, build_status_request(), expect_cmd="devStatus", timeout=timeout)
    if result:
        return DeviceStatus.from_status_response(result["msg"]["data"])
    return None
