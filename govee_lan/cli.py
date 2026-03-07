"""Command-line interface for govee-lan."""

from __future__ import annotations

import argparse
import sys

from govee_lan.controller import (
    get_status,
    list_scenes,
    set_brightness,
    set_color,
    set_color_temp,
    set_scene,
    turn_off,
    turn_on,
)
from govee_lan.scanner import scan


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="govee", description="Govee LAN API controller")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="Discover Govee devices on the network")

    p_on = sub.add_parser("on", help="Turn device on")
    p_on.add_argument("ip", help="Device IP address")

    p_off = sub.add_parser("off", help="Turn device off")
    p_off.add_argument("ip", help="Device IP address")

    p_br = sub.add_parser("brightness", help="Set brightness (1-100)")
    p_br.add_argument("ip", help="Device IP address")
    p_br.add_argument("value", type=int, help="Brightness percentage (1-100)")

    p_col = sub.add_parser("color", help="Set RGB color")
    p_col.add_argument("ip", help="Device IP address")
    p_col.add_argument("r", type=int, help="Red (0-255)")
    p_col.add_argument("g", type=int, help="Green (0-255)")
    p_col.add_argument("b", type=int, help="Blue (0-255)")

    p_ct = sub.add_parser("colortemp", help="Set color temperature (2000-9000K)")
    p_ct.add_argument("ip", help="Device IP address")
    p_ct.add_argument("kelvin", type=int, help="Color temperature in Kelvin")

    p_st = sub.add_parser("status", help="Query device status")
    p_st.add_argument("ip", help="Device IP address")

    p_scenes = sub.add_parser("scenes", help="List available scenes for a device SKU")
    p_scenes.add_argument("sku", help="Device SKU (e.g. H6076)")

    p_scene = sub.add_parser("scene", help="Activate a scene on a device")
    p_scene.add_argument("ip", help="Device IP address")
    p_scene.add_argument("sku", help="Device SKU (e.g. H6076)")
    p_scene.add_argument("name", nargs="+", help="Scene name (e.g. Rainbow)")

    args = parser.parse_args(argv)

    match args.command:
        case "scan":
            _do_scan()
        case "on":
            turn_on(args.ip)
            print(f"Turned on {args.ip}")
        case "off":
            turn_off(args.ip)
            print(f"Turned off {args.ip}")
        case "brightness":
            set_brightness(args.ip, args.value)
            print(f"Set brightness to {args.value}% on {args.ip}")
        case "color":
            set_color(args.ip, args.r, args.g, args.b)
            print(f"Set color to ({args.r}, {args.g}, {args.b}) on {args.ip}")
        case "colortemp":
            set_color_temp(args.ip, args.kelvin)
            print(f"Set color temperature to {args.kelvin}K on {args.ip}")
        case "status":
            _do_status(args.ip)
        case "scenes":
            _do_list_scenes(args.sku)
        case "scene":
            scene_name = " ".join(args.name)
            _do_set_scene(args.ip, args.sku, scene_name)


def _do_scan() -> None:
    print("Scanning for Govee devices...")
    devices = scan()
    if not devices:
        print("No devices found. Make sure LAN API is enabled in the Govee Home app.")
        return
    print(f"\nFound {len(devices)} device(s):\n")
    for d in devices:
        print(f"  IP:     {d.ip}")
        print(f"  ID:     {d.device_id}")
        print(f"  SKU:    {d.sku}")
        print(f"  BLE:    HW {d.ble_version_hard}  SW {d.ble_version_soft}")
        print(f"  WiFi:   HW {d.wifi_version_hard}  SW {d.wifi_version_soft}")
        print()


def _do_status(ip: str) -> None:
    status = get_status(ip)
    if not status:
        print(f"No response from {ip} (is LAN API enabled?)")
        sys.exit(1)
    state = "ON" if status.on else "OFF"
    print(f"Device {ip}:")
    print(f"  State:       {state}")
    print(f"  Brightness:  {status.brightness}%")
    print(f"  Color:       R={status.color_r} G={status.color_g} B={status.color_b}")
    print(f"  Color Temp:  {status.color_temp_kelvin}K")


def _do_list_scenes(sku: str) -> None:
    print(f"Fetching scenes for {sku}...")
    names = list_scenes(sku)
    if not names:
        print(f"No scenes found for {sku}.")
        return
    print(f"\n{len(names)} scene(s) available:\n")
    for name in names:
        print(f"  {name}")


def _do_set_scene(ip: str, sku: str, scene_name: str) -> None:
    try:
        scene = set_scene(ip, sku, scene_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Activated scene {scene.name!r} on {ip}")


if __name__ == "__main__":
    main()
