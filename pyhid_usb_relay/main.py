#! /usr/bin/env python3
#
# Copyright 2021 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import sys
import time
from pyhid_usb_relay import find, DeviceNotFoundError


def main():
    def onoff(state):
        if state:
            return "on"
        return "off"

    def print_status(d):
        print("Board ID=[%s] State: %02x" % (d.serial, d.state))

    def pulse_sleep(d, relay):
        time.sleep(d.get_property(relay, "pulse-time", 1.0))

    def set_relay(args, value):
        device = find(serial=args.serial)

        device[args.relay] = value

        if args.pulse:
            pulse_sleep(device, args.relay)
            device[args.relay] = not value

    def relay_enum(args):
        devices = find(find_all=True)
        if devices is not None:
            for d in devices:
                print_status(d)

    def relay_state(args):
        device = find(serial=args.serial)

        print_status(device)
        for i in range(1, device.num_relays + 1):
            print("%d: %s" % (i, onoff(device[i])))
        for a in device.aliases.keys():
            print("%s: %s" % (a, onoff(device[a])))

    def relay_on(args):
        set_relay(args, True)

    def relay_off(args):
        set_relay(args, False)

    def relay_toggle(args):
        device = find(serial=args.serial)
        device.toggle_state(args.relay)

        if args.pulse:
            pulse_sleep(device, args.relay)
            device.toggle_state(args.relay)

    def relay_get(args):
        device = find(serial=args.serial)
        print(onoff(device[args.relay]))

    def relay_get_serial(args):
        try:
            device = find(bus=args.bus, address=args.address)
            print(device.serial)
        except DeviceNotFoundError:
            return 1

    def relay_set_serial(args):
        try:
            if args.bus:
                device = find(bus=args.bus[0], address=args.bus[1])
            else:
                device = find(serial=args.serial)

            device.set_serial(args.new_serial)

        except DeviceNotFoundError:
            return 1

    parser = argparse.ArgumentParser(description="USB HID Relay control")

    subparser = parser.add_subparsers(title="Subcommands", dest="cmd")
    subparser.required = True

    enum_parser = subparser.add_parser("enum", help="Enumerate devices")
    enum_parser.set_defaults(func=relay_enum)

    state_parser = subparser.add_parser("state", help="Show device state")
    state_parser.set_defaults(func=relay_state)
    state_parser.add_argument("--serial", help="Control board with given serial ID")

    on_parser = subparser.add_parser("on", help="Turn relay on")
    on_parser.add_argument(
        "relay", help='Relay to control. Numeric ID, a defined alias, or "all"'
    )
    on_parser.add_argument("--serial", help="Control board with given serial ID")
    on_parser.add_argument(
        "--pulse", help="Turn on for a short time, then off", action="store_true"
    )
    on_parser.set_defaults(func=relay_on)

    off_parser = subparser.add_parser("off", help="Turn relay off")
    off_parser.add_argument(
        "relay", help='Relay to control. Numeric ID, a defined alias, or "all"'
    )
    off_parser.add_argument("--serial", help="Control board with given serial ID")
    off_parser.add_argument(
        "--pulse", help="Turn off for a short time, then on", action="store_true"
    )
    off_parser.set_defaults(func=relay_off)

    toggle_parser = subparser.add_parser("toggle", help="Toggle relay")
    toggle_parser.add_argument(
        "relay", help='Relay to control. Numeric ID, a defined alias, or "all"'
    )
    toggle_parser.add_argument("--serial", help="Control board with given serial ID")
    toggle_parser.add_argument(
        "--pulse", help="Change state for a short time, then back", action="store_true"
    )
    toggle_parser.set_defaults(func=relay_toggle)

    get_parser = subparser.add_parser("get", help="Get relay state")
    get_parser.add_argument(
        "relay", help='Relay to get. Numeric ID, a defined alias, or "all"'
    )
    get_parser.add_argument("--serial", help="Control board with given serial ID")
    get_parser.set_defaults(func=relay_get)

    get_serial_parser = subparser.add_parser(
        "get-serial", help="Get device serial number"
    )
    get_serial_parser.add_argument("bus", type=int, help="Device USB bus number")
    get_serial_parser.add_argument("address", type=int, help="Device USB address")
    get_serial_parser.set_defaults(func=relay_get_serial)

    set_serial_parser = subparser.add_parser(
        "set-serial", help="Set device serial number"
    )
    group = set_serial_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--bus",
        nargs=2,
        metavar=("BUS", "ADDRESS"),
        type=int,
        help="Device USB bus number and address",
    )
    group.add_argument("--serial", help="Control board with given serial ID")
    set_serial_parser.add_argument("new_serial", help="New serial number")
    set_serial_parser.set_defaults(func=relay_set_serial)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, IndexError, DeviceNotFoundError) as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1
