# Copyright 2024 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import subprocess
import sys

import pyhid_usb_relay


def test_version():
    p = subprocess.run(
        [
            "pyhid-usb-relay",
            "--version",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout.rstrip() == pyhid_usb_relay.VERSION


def test_module_version():
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyhid_usb_relay",
            "--version",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout.rstrip() == pyhid_usb_relay.VERSION
