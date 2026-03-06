"""Device discovery via the Govee LAN API."""

from __future__ import annotations

from govee_lan.device import GoveeDevice
from govee_lan.protocol import (
    BROADCAST_ADDR,
    DEFAULT_SCAN_TIMEOUT,
    DISCOVERY_PORT,
    MULTICAST_GROUP,
    build_scan,
)
from govee_lan.transport import (
    get_local_ip,
    get_subnet_broadcast,
    make_listener,
    make_sender,
    recv_responses,
)


def scan(timeout: float = DEFAULT_SCAN_TIMEOUT, *, unicast_sweep: bool = True) -> list[GoveeDevice]:
    """Discover Govee devices on the local network.

    Sends scan requests via multicast, subnet broadcast, global broadcast,
    and optionally a unicast sweep to every address in the /24 subnet.

    Returns a deduplicated list of discovered devices.
    """
    local_ip = get_local_ip()
    subnet_broadcast = get_subnet_broadcast(local_ip)
    subnet_prefix = ".".join(local_ip.split(".")[:3])

    listener = make_listener()
    sender = make_sender(local_ip)

    payload = build_scan()
    for addr in [
        (MULTICAST_GROUP, DISCOVERY_PORT),
        (subnet_broadcast, DISCOVERY_PORT),
        (BROADCAST_ADDR, DISCOVERY_PORT),
    ]:
        sender.sendto(payload, addr)

    if unicast_sweep:
        for i in range(1, 255):
            ip = f"{subnet_prefix}.{i}"
            if ip == local_ip:
                continue
            try:
                sender.sendto(payload, (ip, DISCOVERY_PORT))
            except OSError:
                continue

    responses = recv_responses(listener, timeout)
    sender.close()
    listener.close()

    seen: set[str] = set()
    devices: list[GoveeDevice] = []
    for msg, addr in responses:
        try:
            data = msg["msg"]["data"]
            device_id = data.get("device", addr)
            if device_id in seen:
                continue
            seen.add(device_id)
            devices.append(GoveeDevice.from_scan_response(data))
        except (KeyError, TypeError):
            continue
    return devices
