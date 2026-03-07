"""Govee LAN API protocol constants and message builders."""

from __future__ import annotations

import base64
import json
import math

MULTICAST_GROUP = "239.255.255.250"
BROADCAST_ADDR = "255.255.255.255"
DISCOVERY_PORT = 4001
LISTEN_PORT = 4002
CONTROL_PORT = 4003

DEFAULT_SCAN_TIMEOUT = 3.0
DEFAULT_CMD_TIMEOUT = 3.0

PACKET_LEN = 20
PAYLOAD_LEN = PACKET_LEN - 1  # 19 bytes before checksum


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


def build_pt_real(commands: list[str]) -> bytes:
    """Wrap base64-encoded BLE command strings in a ptReal JSON envelope."""
    return _encode({"cmd": "ptReal", "data": {"command": commands}})


def build_scene_commands(
    scene_code: int,
    scene_param_b64: str,
    scene_type: int,
    *,
    prefix_remove: bytes = b"",
    prefix_add: bytes = b"",
    suffix: bytes = b"",
    multi_prefix: bytes = b"\xa3",
    on_command: bool = False,
) -> list[str]:
    """Build base64 LAN commands for activating a Govee scene.

    Implements the reverse-engineered BLE-over-LAN protocol (v1.2) documented at
    https://github.com/egold555/Govee-Reverse-Engineering/issues/11

    Returns a list of base64-encoded 20-byte packet strings ready for ``build_pt_real``.
    """
    commands: list[str] = []

    if on_command:
        pkt = b"\x33\x01\x01" + b"\x00" * 16
        commands.append(_b64_packet(pkt))

    scene_param = base64.b64decode(scene_param_b64) if scene_param_b64 else b""

    if scene_param:
        if prefix_remove and scene_param.startswith(prefix_remove):
            scene_param = scene_param[len(prefix_remove) :]
        if prefix_add:
            scene_param = prefix_add + scene_param

        # Prepend start-byte (0x01), num_lines, and sceneType
        data_with_header = b"\x01" + b"\x00" + scene_type.to_bytes(1) + scene_param
        chunk_size = PAYLOAD_LEN - 2  # subtract multi_prefix (1) + index (1)
        num_lines = math.ceil(len(data_with_header) / chunk_size)
        # Patch num_lines into the header
        data_with_header = b"\x01" + num_lines.to_bytes(1) + scene_type.to_bytes(1) + scene_param

        for i in range(num_lines):
            idx = b"\xff" if i == num_lines - 1 else i.to_bytes(1)
            chunk = data_with_header[i * chunk_size : (i + 1) * chunk_size]
            pkt = multi_prefix + idx + chunk
            pkt = pkt.ljust(PAYLOAD_LEN, b"\x00")
            commands.append(_b64_packet(pkt))

    # Standard "modeCmd" that selects the scene in the app
    code_bytes = scene_code.to_bytes(max(1, (scene_code.bit_length() + 7) // 8), byteorder="little")
    mode_pkt = b"\x33\x05\x04" + code_bytes + suffix
    mode_pkt = mode_pkt.ljust(PAYLOAD_LEN, b"\x00")
    commands.append(_b64_packet(mode_pkt))

    return commands


def _xor_checksum(data: bytes) -> int:
    result = 0
    for b in data:
        result ^= b
    return result


def _b64_packet(payload: bytes) -> str:
    """Pad to 19 bytes, append XOR checksum, return base64."""
    payload = payload[:PAYLOAD_LEN].ljust(PAYLOAD_LEN, b"\x00")
    packet = payload + _xor_checksum(payload).to_bytes(1)
    return base64.b64encode(packet).decode("ascii")


def parse_message(data: bytes) -> dict:
    return json.loads(data.decode())


def _encode(msg_body: dict) -> bytes:
    return json.dumps({"msg": msg_body}).encode()
