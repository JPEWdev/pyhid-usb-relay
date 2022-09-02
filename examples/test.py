#! /usr/bin/env python3
import pyhid_usb_relay
import time

if __name__ == "__main__":
    relay = pyhid_usb_relay.find()

    # Example of reading state and toggling relay #1
    if relay.get_state(1):
        relay.toggle_state(1)
    time.sleep(3)

    if not relay.get_state(1):
        relay.toggle_state(1)
    time.sleep(3)

    # You can also refer to relays by index
    if relay[1]:
        relay[1] = False
    time.sleep(3)

    if not relay[1]:
        relay[1] = True
    time.sleep(3)

    # If you have relay aliases defined in your config file, you can also refer
    # to them in place of the index:
    relay["raspberrypi4"] = not relay["raspberrypi4"]
