"""Tests for device controller with mocked sockets."""

import json
from unittest.mock import patch

from govee_lan.controller import (
    _send_to_all,
    get_status,
    set_brightness,
    set_color,
    set_color_temp,
    set_scene_sync,
    turn_off,
    turn_on,
)
from govee_lan.scenes import SceneInfo
from tests.conftest import SAMPLE_STATUS_RESPONSE


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


FAKE_SCENE = SceneInfo(name="Rainbow", scene_code=42, scene_type=2, scene_param="AAAA")


class TestSendToAll:
    def test_sends_to_each_ip(self, mock_sockets):
        payload = b'{"msg":{"cmd":"ptReal","data":{"command":["abc"]}}}'
        _send_to_all(["192.168.1.100", "192.168.1.101"], payload)
        calls = mock_sockets.sender.sendto.call_args_list
        assert len(calls) == 2
        assert calls[0].args == (payload, ("192.168.1.100", 4003))
        assert calls[1].args == (payload, ("192.168.1.101", 4003))

    def test_uses_single_socket(self, mock_sockets):
        _send_to_all(["192.168.1.100", "192.168.1.101"], b"test")
        mock_sockets.mock_make_sender.assert_called_once()

    def test_closes_socket(self, mock_sockets):
        _send_to_all(["192.168.1.100"], b"test")
        mock_sockets.sender.close.assert_called_once()


class TestSetSceneSync:
    @patch("govee_lan.controller.generate_scene_commands", return_value=["cmd1"])
    @patch("govee_lan.controller.fetch_scene_catalog", return_value=[FAKE_SCENE])
    def test_sends_same_payload_to_all_ips(self, mock_catalog, mock_gen, mock_sockets):
        set_scene_sync(["192.168.1.100", "192.168.1.101"], "H6076", "Rainbow")
        calls = mock_sockets.sender.sendto.call_args_list
        assert len(calls) == 2
        assert calls[0].args[0] == calls[1].args[0]
        msg = json.loads(calls[0].args[0])
        assert msg["msg"]["cmd"] == "ptReal"

    @patch("govee_lan.controller.generate_scene_commands", return_value=["cmd1"])
    @patch("govee_lan.controller.fetch_scene_catalog", return_value=[FAKE_SCENE])
    def test_fetches_catalog_once(self, mock_catalog, mock_gen, mock_sockets):
        set_scene_sync(["192.168.1.100", "192.168.1.101"], "H6076", "Rainbow")
        mock_catalog.assert_called_once_with("H6076")

    @patch("govee_lan.controller.generate_scene_commands", return_value=["cmd1"])
    @patch("govee_lan.controller.fetch_scene_catalog", return_value=[FAKE_SCENE])
    def test_returns_scene_info(self, mock_catalog, mock_gen, mock_sockets):
        result = set_scene_sync(["192.168.1.100"], "H6076", "Rainbow")
        assert result.name == "Rainbow"
        assert result.scene_code == 42

    @patch("govee_lan.controller.fetch_scene_catalog", return_value=[FAKE_SCENE])
    def test_raises_on_unknown_scene(self, mock_catalog, mock_sockets):
        import pytest

        with pytest.raises(ValueError, match="not found"):
            set_scene_sync(["192.168.1.100"], "H6076", "Nonexistent")
