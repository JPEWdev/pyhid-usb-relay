# Copyright 2024 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import subprocess
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
