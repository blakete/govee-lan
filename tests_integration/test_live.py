"""Integration tests against real Govee devices on the local network.

Run with:  .venv/bin/pytest tests_integration/ -v -s

Requires tests_integration/local_config.json with:
  {"device_ips": ["192.168.86.x", ...]}

This file is gitignored and should NOT be committed.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from govee_lan import scan
from govee_lan.device import GoveeDevice

CONFIG_PATH = Path(__file__).parent / "local_config.json"


def _load_ips() -> list[str]:
    if not CONFIG_PATH.exists():
        pytest.skip("No local_config.json found -- skipping live tests")
    with open(CONFIG_PATH) as f:
        return json.load(f)["device_ips"]


@pytest.fixture(scope="module")
def device_ips() -> list[str]:
    return _load_ips()


@pytest.fixture
def device(device_ips: list[str]) -> GoveeDevice:
    return GoveeDevice(ip=device_ips[0], device_id="", sku="")


class TestLiveScan:
    def test_discovers_devices(self, device_ips):
        devices = scan(timeout=5.0)
        found_ips = {d.ip for d in devices}
        for ip in device_ips:
            assert ip in found_ips, f"Expected to find {ip} in scan results"


class TestLiveControl:
    def test_turn_on_and_status(self, device):
        device.turn_on()
        time.sleep(0.5)
        status = device.get_status(timeout=5.0)
        assert status is not None
        assert status.on is True

    def test_set_brightness(self, device):
        device.turn_on()
        time.sleep(0.3)
        device.set_brightness(50)
        time.sleep(0.5)
        status = device.get_status(timeout=5.0)
        assert status is not None
        assert status.brightness == 50

    def test_set_color(self, device):
        device.set_color(0, 255, 0)
        time.sleep(0.5)
        status = device.get_status(timeout=5.0)
        assert status is not None
        assert status.color_g == 255

    def test_set_color_temp(self, device):
        device.set_color_temp(4000)
        time.sleep(0.5)
        status = device.get_status(timeout=5.0)
        assert status is not None
        assert status.color_temp_kelvin == 4000

    def test_turn_off(self, device):
        device.turn_off()
        time.sleep(0.5)
        status = device.get_status(timeout=5.0)
        assert status is not None
        assert status.on is False

    def test_restore_on(self, device):
        """Leave the lamp on after tests."""
        device.turn_on()
        device.set_color_temp(6500)
        device.set_brightness(100)
