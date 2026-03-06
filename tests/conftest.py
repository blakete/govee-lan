"""Shared fixtures for Govee LAN tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

SAMPLE_SCAN_RESPONSE = {
    "msg": {
        "cmd": "scan",
        "data": {
            "ip": "192.168.1.100",
            "device": "AA:BB:CC:DD:EE:FF:11:22",
            "sku": "H6076",
            "bleVersionHard": "3.01.01",
            "bleVersionSoft": "1.04.08",
            "wifiVersionHard": "1.00.10",
            "wifiVersionSoft": "1.02.11",
        },
    }
}

SAMPLE_SCAN_RESPONSE_2 = {
    "msg": {
        "cmd": "scan",
        "data": {
            "ip": "192.168.1.101",
            "device": "11:22:33:44:55:66:77:88",
            "sku": "H6076",
            "bleVersionHard": "3.01.01",
            "bleVersionSoft": "1.04.08",
            "wifiVersionHard": "1.00.10",
            "wifiVersionSoft": "1.02.11",
        },
    }
}

SAMPLE_STATUS_RESPONSE = {
    "msg": {
        "cmd": "devStatus",
        "data": {
            "onOff": 1,
            "brightness": 75,
            "color": {"r": 255, "g": 128, "b": 0},
            "colorTemInKelvin": 0,
        },
    }
}


@pytest.fixture
def mock_sockets():
    """Patch transport functions in both scanner and controller modules.

    Yields a namespace with:
      - listener: the mock listener socket
      - sender: the mock sender socket
      - set_responses(list[tuple[dict, str]]): queue responses for recv_responses
      - mock_recv: the patched recv_responses callable (from controller)
      - mock_make_listener: the patched make_listener callable (from controller)
    """
    listener = MagicMock()
    sender = MagicMock()
    responses: list[tuple[dict, str]] = []

    # scanner imports: make_listener, make_sender, recv_responses, get_local_ip, get_subnet_broadcast
    # controller imports: make_listener, make_sender, recv_responses
    all_patches = [
        patch("govee_lan.scanner.make_listener", return_value=listener),
        patch("govee_lan.scanner.make_sender", return_value=sender),
        patch("govee_lan.scanner.get_local_ip", return_value="192.168.1.50"),
        patch("govee_lan.scanner.get_subnet_broadcast", return_value="192.168.1.255"),
        patch("govee_lan.controller.make_listener", return_value=listener),
        patch("govee_lan.controller.make_sender", return_value=sender),
    ]

    recv_patches = [
        patch("govee_lan.scanner.recv_responses"),
        patch("govee_lan.controller.recv_responses"),
    ]

    started = [p.start() for p in all_patches]
    recv_mocks = [p.start() for p in recv_patches]
    for mk in recv_mocks:
        mk.return_value = responses

    def _set_responses(resps: list[tuple[dict, str]]) -> None:
        responses.clear()
        responses.extend(resps)
        for mk in recv_mocks:
            mk.return_value = list(responses)

    ns = MagicMock()
    ns.listener = listener
    ns.sender = sender
    ns.set_responses = _set_responses
    ns.mock_recv = recv_mocks[1]  # controller recv
    ns.scanner_recv = recv_mocks[0]  # scanner recv
    ns.mock_make_listener = started[4]  # controller make_listener
    ns.mock_make_sender = started[5]  # controller make_sender

    yield ns

    for p in all_patches + recv_patches:
        p.stop()
