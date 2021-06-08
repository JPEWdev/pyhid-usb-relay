#! /usr/bin/env python3
#
# Copyright 2020 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import array
import os
import sys
import time
import usb.core
import usb.util
import xdg
import yaml

VENDOR_ID = 0x16C0
PRODUCT_ID = 0x05DF
USB_TYPE_CLASS = 0x20
USB_ENDPOINT_OUT = 0x00
USB_ENDPOINT_IN = 0x80
USB_RECIP_DEVICE = 0x00
GET_REPORT = 0x1
SET_REPORT = 0x9
USB_HID_REPORT_TYPE_FEATURE = 3
MAIN_REPORT = 0


def xor(a, b):
    return bool(a) != bool(b)


class Controller(object):
    def __init__(self, device, timeout=5000):
        self.device = device
        self.timeout = timeout
        self.product = usb.util.get_string(device, device.iProduct)
        self.num_relays = int(self.product[8:])

        self._update_status()

        self.aliases = {}
        self.defaults = {}

        try:
            with open(
                os.path.join(xdg.XDG_CONFIG_HOME, "usb-hid-relay", "config.yaml"), "r"
            ) as f:
                config = yaml.load(f, Loader=yaml.Loader)

            if self.serial in config:
                self.aliases = config[self.serial].get("aliases", {})
                self.defaults = config[self.serial].get("defaults", {})

        except FileNotFoundError:
            pass

    def get_property(self, relay, name, default=None):
        value = self.defaults.get(name, default)
        if relay != "all" and relay in self.aliases:
            value = self.aliases[relay].get(name, value)
        return value

    def _update_status(self):
        data = self._get_hid_report(MAIN_REPORT, 8)
        self.serial = data[0:5].tobytes().decode("utf-8")
        self.state = data[7]

    def _name_to_number(self, relay):
        def convert():
            invert = self.defaults.get("invert", False)

            try:
                if relay in self.aliases:
                    return (
                        int(self.aliases[relay]["relay"]),
                        self.aliases[relay].get("invert", invert),
                    )

                return (int(relay), invert)
            except ValueError:
                pass

            raise ValueError("'%s' is not a valid relay descriptor" % relay)

        relay_num, invert = convert()
        if relay_num < 1 or relay_num > self.num_relays:
            raise IndexError(
                "Index %r is outside range [1..%d]" % (relay_num, self.num_relays)
            )

        return relay_num

    def _name_to_index(self, relay):
        relay_num = self._name_to_number(relay)
        return relay_num - 1

    def get_state(self, relay):
        self._update_status()
        idx = self._name_to_index(relay)
        invert = self.get_property(relay, "invert", False)

        if self.state & (1 << idx):
            return xor(True, invert)
        return xor(False, invert)

    def set_state(self, relay, state):
        buf = array.array("B")
        invert = self.get_property(relay, "invert", False)
        if relay == "all":
            buf.append(0xFE if xor(state, invert) else 0xFC)
        else:
            relay_num = self._name_to_number(relay)
            buf.append(0xFF if xor(state, invert) else 0xFD)
            buf.append(relay_num)

        self._set_hid_report(MAIN_REPORT, buf)

    def toggle_state(self, relay):
        if relay == "all":
            for i in range(1, self.num_relays + 1):
                self.set_state(i, not self.get_state(i))
        else:
            self.set_state(relay, not self.get_state(relay))

    def __getitem__(self, relay):
        return self.get_state(relay)

    def __setitem__(self, relay, state):
        self.set_state(relay, state)

    def _get_hid_report(self, report, size):
        return self.device.ctrl_transfer(
            USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_IN,
            GET_REPORT,
            (USB_HID_REPORT_TYPE_FEATURE << 8) | report,
            0,
            size,
            self.timeout,
        )

    def _set_hid_report(self, report, data):
        return self.device.ctrl_transfer(
            USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_OUT,
            SET_REPORT,
            (USB_HID_REPORT_TYPE_FEATURE << 8) | report,
            0,
            data,
            self.timeout,
        )


class DeviceNotFoundError(Exception):
    pass


def find(find_all=False, serial=None, bus=None, address=None):
    class match_relay(object):
        def __call__(self, device):
            manufacturer = usb.util.get_string(device, device.iManufacturer)
            product = usb.util.get_string(device, device.iProduct)
            if manufacturer != "www.dcttech.com":
                return False

            if not product.startswith("USBRelay"):
                return False

            if serial is not None:
                c = Controller(device)
                if c.serial != serial:
                    return False

            if bus is not None and device.bus != bus:
                return False

            if address is not None and device.address != address:
                return False

            return True

    devices = usb.core.find(
        find_all=find_all,
        idVendor=VENDOR_ID,
        idProduct=PRODUCT_ID,
        custom_match=match_relay(),
    )

    if devices is None:
        raise DeviceNotFoundError("No device found")

    if find_all:
        devices = [Controller(d) for d in devices]
    else:
        devices = Controller(devices)

    return devices


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

    import argparse

    parser = argparse.ArgumentParser(description="USB HID Relay control")

    subparser = parser.add_subparsers(title="Subcommands")

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

    get_serial_parser = subparser.add_parser("get-serial")
    get_serial_parser.add_argument("bus", type=int, help="Device USB bus number")
    get_serial_parser.add_argument("address", type=int, help="Device USB address")
    get_serial_parser.set_defaults(func=relay_get_serial)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, IndexError, DeviceNotFoundError) as e:
        sys.stderr.write(str(e))
        sys.stderr.write("\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
