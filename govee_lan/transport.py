"""Low-level UDP transport for sending and receiving Govee LAN API messages."""

from __future__ import annotations

import json
import select
import socket
import struct
import time

from govee_lan.protocol import LISTEN_PORT


def make_listener() -> socket.socket:
    """Bind a UDP socket on port 4002 to receive Govee device responses."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("", LISTEN_PORT))
    sock.setblocking(False)
    return sock


def make_sender(local_ip: str | None = None) -> socket.socket:
    """Create a UDP socket for sending commands and discovery packets."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    ttl = struct.pack("b", 2)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    if local_ip:
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(local_ip),
        )
    return sock


def recv_responses(listener: socket.socket, timeout: float) -> list[tuple[dict, str]]:
    """Collect decoded JSON responses from the listener until timeout expires."""
    results: list[tuple[dict, str]] = []
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        ready, _, _ = select.select([listener], [], [], remaining)
        if not ready:
            break
        try:
            data, addr = listener.recvfrom(4096)
            msg = json.loads(data.decode())
            results.append((msg, addr[0]))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return results


def get_local_ip() -> str:
    """Detect the local IP of the primary network interface."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "0.0.0.0"


def get_subnet_broadcast(local_ip: str) -> str:
    """Derive the /24 broadcast address from a local IP."""
    parts = local_ip.split(".")
    parts[3] = "255"
    return ".".join(parts)
