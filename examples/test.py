import pyhid_usb_relay

def off(relay):
    # If relay state is on (1) then we can turn it off.
    if relay.state:
        relay.toggle_state(1)
    else:
        print("The relay is already off")

def on(relay):
    # If relay state is not on (1) then we can turn it on.
    if not relay.state:
        relay.toggle_state(1)
    else:
        print("The relay is already on")

if __name__ == '__main__':
    relay1 = pyhid_usb_relay.find()
    # Turns on the relay
    on(relay1) 
    # You can also turn it off with this helper function
    # off(relay1)
