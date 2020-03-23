Python Utility for controlling HID USB Relays

This utility is a Python version of [usb-relay-hid](https://github.com/pavel-a/usb-relay-hid)

# Getting Started

This project uses [pipenv](https://github.com/pypa/pipenv) to make dependency
management easy. You can either manually install all the dependencies listed in
the [Pipfile](./Pipfile), or start a shell that automatically has all the
correct dependencies with:

```shell
pipenv shell
```

The `relay.py` command is pretty much the same as the `hidusb-relay-cmd` from
the `usb-relay-hid` project, and aims to be feature compatible. Additional
commands are implemented, and the best way to discover what options are
available is to run

```shell
./relay.py --help
```

# Configuration

Coming soon

# Permissions

If you want to access the relay devices as a normal user (which is recommended,
since it will respect your local configuration), you will need to modify your
udev rules to allow access to the HID device. You can do this by creating a
file named `/etc/udev/rules.d/90-hidusb-relay.rules` with the following
contents:

```
# Give all users access to USB HID Relay
SUBSYSTEM=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="05df", MODE:="0660", GROUP="dialout"
```

You may need to reload your udev rules with `sudo udevadm control
--reload-rules` and unplug and reattach the USB relay board for this to take
effect

**NOTE** This rule allows any user that is part of the `dialout` group to
access the board. If this is not what you want, you should change the udev
rules.

