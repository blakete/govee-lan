"""Tests for protocol message builders."""

import json

from govee_lan.protocol import (
    build_brightness,
    build_color,
    build_color_temp,
    build_scan,
    build_status_request,
    build_turn,
    parse_message,
)


def _decode(payload: bytes) -> dict:
    return json.loads(payload.decode())


class TestBuildScan:
    def test_structure(self):
        msg = _decode(build_scan())
        assert msg["msg"]["cmd"] == "scan"
        assert msg["msg"]["data"]["account_topic"] == "reserve"


class TestBuildTurn:
    def test_on(self):
        msg = _decode(build_turn(on=True))
        assert msg["msg"]["cmd"] == "turn"
        assert msg["msg"]["data"]["value"] == 1

    def test_off(self):
        msg = _decode(build_turn(on=False))
        assert msg["msg"]["data"]["value"] == 0


class TestBuildBrightness:
    def test_normal_value(self):
        msg = _decode(build_brightness(50))
        assert msg["msg"]["cmd"] == "brightness"
        assert msg["msg"]["data"]["value"] == 50

    def test_clamped_low(self):
        msg = _decode(build_brightness(-10))
        assert msg["msg"]["data"]["value"] == 1

    def test_clamped_high(self):
        msg = _decode(build_brightness(200))
        assert msg["msg"]["data"]["value"] == 100


class TestBuildColor:
    def test_normal(self):
        msg = _decode(build_color(255, 128, 0))
        data = msg["msg"]["data"]
        assert data["color"] == {"r": 255, "g": 128, "b": 0}
        assert data["colorTemInKelvin"] == 0

    def test_clamped(self):
        msg = _decode(build_color(-5, 300, 128))
        c = msg["msg"]["data"]["color"]
        assert c["r"] == 0
        assert c["g"] == 255
        assert c["b"] == 128


class TestBuildColorTemp:
    def test_normal(self):
        msg = _decode(build_color_temp(4000))
        data = msg["msg"]["data"]
        assert data["colorTemInKelvin"] == 4000
        assert data["color"] == {"r": 0, "g": 0, "b": 0}

    def test_clamped_low(self):
        msg = _decode(build_color_temp(100))
        assert msg["msg"]["data"]["colorTemInKelvin"] == 2000

    def test_clamped_high(self):
        msg = _decode(build_color_temp(20000))
        assert msg["msg"]["data"]["colorTemInKelvin"] == 9000


class TestBuildStatusRequest:
    def test_structure(self):
        msg = _decode(build_status_request())
        assert msg["msg"]["cmd"] == "devStatus"
        assert msg["msg"]["data"] == {}


class TestParseMessage:
    def test_roundtrip(self):
        original = build_scan()
        parsed = parse_message(original)
        assert parsed["msg"]["cmd"] == "scan"
