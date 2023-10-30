# Copyright 2021 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import usb.core
import usb.util

from .controller import Controller
from .exceptions import DeviceNotFoundError

VENDOR_ID = 0x16C0
PRODUCT_ID = 0x05DF


def _get_backend():
    import os

    if os.name != "nt":
        return None

    import usb.backend.libusb1
    import libusb
    import pathlib

    # Manually find the libusb DLL and create a backend using it. I don't know
    # why Python can't find this on its own
    libpath = next(pathlib.Path(libusb.__file__).parent.rglob("x64/libusb-1.0.dll"))
    return usb.backend.libusb1.get_backend(find_library=lambda x: libpath)


def find(*, find_all=False, serial=None, bus=None, address=None):
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
        backend=_get_backend(),
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
