"""Tests for device controller with mocked sockets."""

import json

from tests.conftest import SAMPLE_STATUS_RESPONSE

from govee_lan.controller import (
    get_status,
    set_brightness,
    set_color,
    set_color_temp,
    turn_off,
    turn_on,
)


class TestTurnOn:
    def test_sends_turn_on(self, mock_sockets):
        turn_on("192.168.1.100")
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["cmd"] == "turn"
        assert msg["msg"]["data"]["value"] == 1

    def test_sends_to_correct_port(self, mock_sockets):
        turn_on("192.168.1.100")
        addr = mock_sockets.sender.sendto.call_args.args[1]
        assert addr == ("192.168.1.100", 4003)


class TestTurnOff:
    def test_sends_turn_off(self, mock_sockets):
        turn_off("10.0.0.5")
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["data"]["value"] == 0


class TestSetBrightness:
    def test_sends_brightness(self, mock_sockets):
        set_brightness("192.168.1.100", 42)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["cmd"] == "brightness"
        assert msg["msg"]["data"]["value"] == 42


class TestSetColor:
    def test_sends_color(self, mock_sockets):
        set_color("192.168.1.100", 100, 200, 50)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["data"]["color"] == {"r": 100, "g": 200, "b": 50}
        assert msg["msg"]["data"]["colorTemInKelvin"] == 0


class TestSetColorTemp:
    def test_sends_color_temp(self, mock_sockets):
        set_color_temp("192.168.1.100", 5000)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["data"]["colorTemInKelvin"] == 5000
        assert msg["msg"]["data"]["color"] == {"r": 0, "g": 0, "b": 0}


class TestGetStatus:
    def test_returns_status(self, mock_sockets):
        mock_sockets.mock_recv.return_value = [(SAMPLE_STATUS_RESPONSE, "192.168.1.100")]
        status = get_status("192.168.1.100")
        assert status is not None
        assert status.on is True
        assert status.brightness == 75
        assert status.color_r == 255
        assert status.color_g == 128
        assert status.color_b == 0
        assert status.color_temp_kelvin == 0

    def test_returns_none_on_timeout(self, mock_sockets):
        mock_sockets.mock_recv.return_value = []
        status = get_status("192.168.1.100", timeout=0.1)
        assert status is None

    def test_creates_listener(self, mock_sockets):
        mock_sockets.mock_recv.return_value = []
        get_status("192.168.1.100")
        mock_sockets.mock_make_listener.assert_called()
