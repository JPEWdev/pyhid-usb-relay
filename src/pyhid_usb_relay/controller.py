# Copyright 2021 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import array
import os
import usb.core
import usb.util
import xdg
import yaml

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

    def set_serial(self, new_serial):
        buf = array.array("B")
        buf.append(0xFA)
        serial = new_serial.encode("utf-8")
        for i in range(5):
            if i < len(serial):
                buf.append(serial[i])
            else:
                buf.append(0x00)
        buf.append(0x00)
        buf.append(0x00)
        self._set_hid_report(MAIN_REPORT, buf)

        self._update_status()


    def _update_status(self):
        data = self._get_hid_report(MAIN_REPORT, 8)
        try:
            self.serial = data[0:5].tobytes().decode("utf-8")
        except UnicodeDecodeError:
            self.serial = "".join("%02x" % b for b in data[0:5])
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
