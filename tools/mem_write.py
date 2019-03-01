#!/usr/bin/env python3
from trezorlib.ui import ClickUI
from trezorlib.debuglink import DebugLink
from trezorlib.client import TrezorClient
from trezorlib.transport import enumerate_devices
import sys


def main():
    # List all debuggable TREZORs
    devices = [device for device in enumerate_devices() if hasattr(device, 'find_debug')]

    # Try to get debug transport on devices
    debug_transport = None
    for dev in devices:
        try:
            transport = dev
            debug_transport = dev.find_debug()
            break
        except Exception:
            pass

    # Check whether we found any
    if len(devices) == 0:
        print('No TREZOR found')
        return

    # Check if its available
    if not debug_transport:
        print('Debug device not available')
        return

    # Creates object for manipulating TREZOR
    client = TrezorClient(transport, ui=ClickUI())
    debug = DebugLink(debug_transport)

    debug.memory_write(int(sys.argv[1], 16), bytes.fromhex(sys.argv[2]), flash=True)
    client.close()


if __name__ == '__main__':
    main()
