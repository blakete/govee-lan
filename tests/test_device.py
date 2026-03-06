"""Tests for device data classes."""

import json

import pytest

from govee_lan.device import DeviceStatus, GoveeDevice
from tests.conftest import SAMPLE_STATUS_RESPONSE


class TestGoveeDevice:
    def test_from_scan_response(self):
        data = {
            "ip": "192.168.1.100",
            "device": "AA:BB:CC:DD:EE:FF:11:22",
            "sku": "H6076",
            "bleVersionHard": "3.01.01",
            "bleVersionSoft": "1.04.08",
            "wifiVersionHard": "1.00.10",
            "wifiVersionSoft": "1.02.11",
        }
        dev = GoveeDevice.from_scan_response(data)
        assert dev.ip == "192.168.1.100"
        assert dev.device_id == "AA:BB:CC:DD:EE:FF:11:22"
        assert dev.sku == "H6076"
        assert dev.ble_version_hard == "3.01.01"
        assert dev.wifi_version_soft == "1.02.11"

    def test_from_scan_response_missing_fields(self):
        dev = GoveeDevice.from_scan_response({"ip": "10.0.0.1"})
        assert dev.ip == "10.0.0.1"
        assert dev.device_id == ""
        assert dev.sku == ""

    def test_frozen(self):
        dev = GoveeDevice(ip="1.2.3.4", device_id="x", sku="H1234")
        with pytest.raises(AttributeError):
            dev.ip = "5.6.7.8"  # type: ignore[misc]


class TestDeviceStatus:
    def test_from_status_response_on(self):
        data = {
            "onOff": 1,
            "brightness": 80,
            "color": {"r": 255, "g": 0, "b": 128},
            "colorTemInKelvin": 0,
        }
        status = DeviceStatus.from_status_response(data)
        assert status.on is True
        assert status.brightness == 80
        assert status.color_r == 255
        assert status.color_g == 0
        assert status.color_b == 128
        assert status.color_temp_kelvin == 0

    def test_from_status_response_off(self):
        data = {
            "onOff": 0,
            "brightness": 100,
            "color": {"r": 0, "g": 0, "b": 0},
            "colorTemInKelvin": 6500,
        }
        status = DeviceStatus.from_status_response(data)
        assert status.on is False
        assert status.color_temp_kelvin == 6500

    def test_from_status_response_missing_color(self):
        status = DeviceStatus.from_status_response({"onOff": 1, "brightness": 50})
        assert status.color_r == 0
        assert status.color_g == 0
        assert status.color_b == 0


class TestGoveeDeviceMethods:
    """Test the OOP control methods on GoveeDevice that delegate to controller."""

    @pytest.fixture
    def device(self):
        return GoveeDevice(ip="192.168.1.100", device_id="AA:BB:CC", sku="H6076")

    def test_turn_on(self, device, mock_sockets):
        device.turn_on()
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["cmd"] == "turn"
        assert msg["msg"]["data"]["value"] == 1
        assert mock_sockets.sender.sendto.call_args.args[1] == ("192.168.1.100", 4003)

    def test_turn_off(self, device, mock_sockets):
        device.turn_off()
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["cmd"] == "turn"
        assert msg["msg"]["data"]["value"] == 0

    def test_set_brightness(self, device, mock_sockets):
        device.set_brightness(42)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["cmd"] == "brightness"
        assert msg["msg"]["data"]["value"] == 42

    def test_set_color(self, device, mock_sockets):
        device.set_color(100, 200, 50)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["data"]["color"] == {"r": 100, "g": 200, "b": 50}
        assert msg["msg"]["data"]["colorTemInKelvin"] == 0

    def test_set_color_temp(self, device, mock_sockets):
        device.set_color_temp(5000)
        payload = mock_sockets.sender.sendto.call_args.args[0]
        msg = json.loads(payload)
        assert msg["msg"]["data"]["colorTemInKelvin"] == 5000
        assert msg["msg"]["data"]["color"] == {"r": 0, "g": 0, "b": 0}

    def test_get_status(self, device, mock_sockets):
        mock_sockets.mock_recv.return_value = [(SAMPLE_STATUS_RESPONSE, "192.168.1.100")]
        status = device.get_status()
        assert status is not None
        assert status.on is True
        assert status.brightness == 75
        assert status.color_r == 255

    def test_get_status_timeout(self, device, mock_sockets):
        mock_sockets.mock_recv.return_value = []
        status = device.get_status(timeout=0.1)
        assert status is None
