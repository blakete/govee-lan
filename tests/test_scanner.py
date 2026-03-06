"""Tests for device scanner with mocked sockets."""

from govee_lan.scanner import scan
from tests.conftest import SAMPLE_SCAN_RESPONSE, SAMPLE_SCAN_RESPONSE_2


class TestScan:
    def test_discovers_single_device(self, mock_sockets):
        mock_sockets.set_responses([(SAMPLE_SCAN_RESPONSE, "192.168.1.100")])
        devices = scan(timeout=1.0)
        assert len(devices) == 1
        assert devices[0].ip == "192.168.1.100"
        assert devices[0].sku == "H6076"
        assert devices[0].device_id == "AA:BB:CC:DD:EE:FF:11:22"

    def test_discovers_multiple_devices(self, mock_sockets):
        mock_sockets.set_responses(
            [
                (SAMPLE_SCAN_RESPONSE, "192.168.1.100"),
                (SAMPLE_SCAN_RESPONSE_2, "192.168.1.101"),
            ]
        )
        devices = scan(timeout=1.0)
        assert len(devices) == 2
        ips = {d.ip for d in devices}
        assert ips == {"192.168.1.100", "192.168.1.101"}

    def test_deduplicates_by_device_id(self, mock_sockets):
        mock_sockets.set_responses(
            [
                (SAMPLE_SCAN_RESPONSE, "192.168.1.100"),
                (SAMPLE_SCAN_RESPONSE, "192.168.1.100"),
            ]
        )
        devices = scan(timeout=1.0)
        assert len(devices) == 1

    def test_no_devices(self, mock_sockets):
        mock_sockets.set_responses([])
        devices = scan(timeout=0.1)
        assert devices == []

    def test_ignores_malformed_responses(self, mock_sockets):
        bad = {"not": "valid"}
        mock_sockets.set_responses(
            [
                (bad, "192.168.1.200"),
                (SAMPLE_SCAN_RESPONSE, "192.168.1.100"),
            ]
        )
        devices = scan(timeout=1.0)
        assert len(devices) == 1

    def test_sends_to_multicast_and_broadcasts(self, mock_sockets):
        mock_sockets.set_responses([])
        scan(timeout=0.1, unicast_sweep=False)
        calls = mock_sockets.sender.sendto.call_args_list
        destinations = [c.args[1] for c in calls]
        assert ("239.255.255.250", 4001) in destinations
        assert ("192.168.1.255", 4001) in destinations
        assert ("255.255.255.255", 4001) in destinations
