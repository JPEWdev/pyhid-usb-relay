Python Utility for controlling HID USB Relays

This utility is a Python version of [usb-relay-hid](https://github.com/pavel-a/usb-relay-hid)

# Installation

The latest version can be installed using pip:
```
python3 -m pip install pyhid-usb-relay
```

## Manual Installation

The library can be manually installed using [poetry](https://python-poetry.org/):
```
poetry install
```

From here, you can either run the `pyhid-usb-relay` command with:
```
poetry run pyhid-usb-relay
```

If you want to build a wheel for installation, run
```
poetry build
```

# Usage

## Standalone app outside of python
```shell
pyhid-usb-relay --help
```

## Inside a python app/script
```
import pyhid_usb_relay

relay = pyhid_usb_relay.find()

print(relay.state)
print("Toggeling relay")

relay.toggle_state(1)

print(relay.state)

```

# Configuration

Relay configuration is read from the file
`$XDG_CONFIG_HOME/usb-hid-relay/config.yaml` (usually
`~/.config/usb-hid-relay/config.yaml`). This YAML file should contain a top
level dictionary key for each relay serial number to be configured, like so:

```yaml
5291D:
  defaults:
    ...
  aliases:
    ...
```

The following properties may be defined in the `default` section and apply to
all relays on the board:

* `invert` - A boolean that indicates if the relay logic should be inverted
* `pulse-time` - A floating point number of seconds the relay should remain in
the opposite state when `pyhid-usb-relay toggle --pulse` is called

Aliases are created by adding a new key under `aliases` with a `relay` property
indicating which relay number the alias controls. For example the following
config creates an alias called `foo` that may be used in place of relay number
2 in the API:

```yaml
5219D:
  aliases:
    foo:
      relay: 2
```

Aliases may also define any of the properties listed in `defaults`, in which
case they only apply when the specific alias is used. Note that these
properties apply to the _alias_ not the relay number. Using a relay number in
the API will only apply the defaults

An example configuration is show here:

```yaml
# Define properties for relay board with serial 5291D
5291D:
  defaults:
    invert: true    # Invert all relays by default
    pulse-time: 5.0 # Default pulse time is 5 seconds for this board
  aliases:
    foo:                # Create an alias called "foo"
      relay: 1          # This alias controls relay 1
      invert: false     # Don't invert this alias (overrides the default)
      pulse-time: 1.0   # Override default pulse-time for this alias
```

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

# Fixing Serial Numbers

The relays that this tool is designed to control have a quirk that they all
report the same USB Vendor, Product, and Serial Number (The serial number used
by this code is retrieved by the HID API). This can make it hard to distinguish
between multiple relays attached to the same device using udev rules.

The `pyhid-usb-relay` tool can be used to help resolve this by using the
`get-serial` subcommand, which will fetch the HID serial number from the device
with a udev rule that looks like:

```
SUBSYSTEM=="usb", ATTR{idVendor}=="16c0", ATTR{idProduct}=="05df", ACTION=="add", PROGRAM="/usr/local/bin/pyhid-usb-relay get-serial '%E{BUSNUM}' '%E{DEVNUM}'", ENV{ID_SERIAL}:="%c"
```
