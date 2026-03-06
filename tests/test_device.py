"""Tests for device data classes."""

from govee_lan.device import DeviceStatus, GoveeDevice


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
        try:
            dev.ip = "5.6.7.8"  # type: ignore[misc]
            assert False, "Should not allow mutation"
        except AttributeError:
            pass


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
