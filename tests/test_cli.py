"""Tests for CLI interface."""

from unittest.mock import patch, MagicMock

import pytest

from govee_lan.cli import main
from govee_lan.device import DeviceStatus, GoveeDevice


class TestCliScan:
    @patch("govee_lan.cli.scan")
    def test_scan_no_devices(self, mock_scan, capsys):
        mock_scan.return_value = []
        main(["scan"])
        out = capsys.readouterr().out
        assert "No devices found" in out

    @patch("govee_lan.cli.scan")
    def test_scan_found_devices(self, mock_scan, capsys):
        mock_scan.return_value = [
            GoveeDevice(
                ip="192.168.1.100",
                device_id="AA:BB:CC",
                sku="H6076",
                ble_version_hard="3.01.01",
                ble_version_soft="1.04.08",
                wifi_version_hard="1.00.10",
                wifi_version_soft="1.02.11",
            )
        ]
        main(["scan"])
        out = capsys.readouterr().out
        assert "192.168.1.100" in out
        assert "H6076" in out
        assert "Found 1 device(s)" in out


class TestCliOn:
    @patch("govee_lan.cli.turn_on")
    def test_turn_on(self, mock_turn_on, capsys):
        main(["on", "10.0.0.1"])
        mock_turn_on.assert_called_once_with("10.0.0.1")
        assert "Turned on" in capsys.readouterr().out


class TestCliOff:
    @patch("govee_lan.cli.turn_off")
    def test_turn_off(self, mock_turn_off, capsys):
        main(["off", "10.0.0.1"])
        mock_turn_off.assert_called_once_with("10.0.0.1")
        assert "Turned off" in capsys.readouterr().out


class TestCliBrightness:
    @patch("govee_lan.cli.set_brightness")
    def test_set_brightness(self, mock_brightness, capsys):
        main(["brightness", "10.0.0.1", "75"])
        mock_brightness.assert_called_once_with("10.0.0.1", 75)
        assert "75%" in capsys.readouterr().out


class TestCliColor:
    @patch("govee_lan.cli.set_color")
    def test_set_color(self, mock_color, capsys):
        main(["color", "10.0.0.1", "255", "0", "128"])
        mock_color.assert_called_once_with("10.0.0.1", 255, 0, 128)
        assert "(255, 0, 128)" in capsys.readouterr().out


class TestCliColorTemp:
    @patch("govee_lan.cli.set_color_temp")
    def test_set_colortemp(self, mock_ct, capsys):
        main(["colortemp", "10.0.0.1", "6500"])
        mock_ct.assert_called_once_with("10.0.0.1", 6500)
        assert "6500K" in capsys.readouterr().out


class TestCliStatus:
    @patch("govee_lan.cli.get_status")
    def test_status_found(self, mock_status, capsys):
        mock_status.return_value = DeviceStatus(
            on=True, brightness=80, color_r=255, color_g=0, color_b=0, color_temp_kelvin=0
        )
        main(["status", "10.0.0.1"])
        out = capsys.readouterr().out
        assert "ON" in out
        assert "80%" in out

    @patch("govee_lan.cli.get_status")
    def test_status_timeout(self, mock_status):
        mock_status.return_value = None
        with pytest.raises(SystemExit):
            main(["status", "10.0.0.1"])


class TestCliInvalidArgs:
    def test_no_command(self):
        with pytest.raises(SystemExit):
            main([])
