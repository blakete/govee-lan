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

from govee_lan import scan, turn_on, turn_off, set_brightness, set_color, set_color_temp, get_status

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
def first_ip(device_ips: list[str]) -> str:
    return device_ips[0]


class TestLiveScan:
    def test_discovers_devices(self, device_ips):
        devices = scan(timeout=5.0)
        found_ips = {d.ip for d in devices}
        for ip in device_ips:
            assert ip in found_ips, f"Expected to find {ip} in scan results"


class TestLiveControl:
    def test_turn_on_and_status(self, first_ip):
        turn_on(first_ip)
        time.sleep(0.5)
        status = get_status(first_ip, timeout=5.0)
        assert status is not None
        assert status.on is True

    def test_set_brightness(self, first_ip):
        turn_on(first_ip)
        time.sleep(0.3)
        set_brightness(first_ip, 50)
        time.sleep(0.5)
        status = get_status(first_ip, timeout=5.0)
        assert status is not None
        assert status.brightness == 50

    def test_set_color(self, first_ip):
        set_color(first_ip, 0, 255, 0)
        time.sleep(0.5)
        status = get_status(first_ip, timeout=5.0)
        assert status is not None
        assert status.color_g == 255

    def test_set_color_temp(self, first_ip):
        set_color_temp(first_ip, 4000)
        time.sleep(0.5)
        status = get_status(first_ip, timeout=5.0)
        assert status is not None
        assert status.color_temp_kelvin == 4000

    def test_turn_off(self, first_ip):
        turn_off(first_ip)
        time.sleep(0.5)
        status = get_status(first_ip, timeout=5.0)
        assert status is not None
        assert status.on is False

    def test_restore_on(self, first_ip):
        """Leave the lamp on after tests."""
        turn_on(first_ip)
        set_color_temp(first_ip, 6500)
        set_brightness(first_ip, 100)
