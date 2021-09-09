#! /usr/bin/env python3
# Copyright 2021 Joshua Watt <JPEWhacker@gmail.com>
#
# SPDX-License-Identifier: MIT

import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="pyhid-usb-relay",
    version="0.1.0",
    author="Joshua Watt",
    author_email="JPEWhacker@gmail.com",
    description="A tool for controlling USB HID relays",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JPEWdev/pyhid-usb-relay",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "pyusb",
        "pyyaml",
        "xdg",
    ],
    scripts=[
        "bin/pyhid-usb-relay",
    ],
)
