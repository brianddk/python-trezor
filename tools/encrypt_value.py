#!/usr/bin/env python3
#
# Note, this doesn't use the same address (-n) as Trezor Password Manager
#   By default it will store the address and key in clear text and only
#   encrypt the value.  Use --secure to force the user to name key and
#   address on the command line, and keep it out of the armor file.

from trezorlib import misc, tools, ui
from trezorlib import __version__ as trezor_version
from trezorlib.client import TrezorClient
from trezorlib.transport import get_transport
from random import getrandbits
import sys
import base64
import argparse


def key_to_addr(key):
    addr = []
    try:
        key_hex = bytes.fromhex(key).hex()
    except ValueError:
        key_hex = str.encode(key).hex()
    while len(key_hex):
        addr.append(int(key_hex[:8], 16))
        key_hex = key_hex[8:]
    return addr


def input_key_addr(value, kheader, aheader, args):
    key = getrandbits(key_len * 8).to_bytes(key_len, byteorder='big').hex()
    addr = False
    if args.decrypt:
        for line in value.decode().split('\n'):
            line = line.replace('\r', '')
            words = line.split()
            if words and words[0] == kheader:
                x = len(kheader) + 1
                key = line[x:]
                if not addr:
                    addr = key_to_addr(key)
            if words and words[0] == aheader:
                x = len(aheader) + 1
                addr = tools.parse_path(line[x:])
    if args.key:
        key = args.key
    if args.address:
        addr = tools.parse_path(args.address)
    if not addr:
        addr = key_to_addr(key)
    return key, addr


def pad_value(value):
    p = 16 - len(value) % 16
    for i in range(0, p):
        value += int(p).to_bytes(1, byteorder='big')
    return value


def depad_value(value):
    p = 0 - value[-1]
    return value[:p]


def input_value(args):
    value = sys.stdin.buffer.read()
    if not args.decrypt:
        value = pad_value(value)
    return value


def print_enarmor(binstr):
    astr = base64.standard_b64encode(enc).decode()
    while astr:
        print(astr[:64])
        astr = astr[64:]


def dearmor(value):
    dec = ''
    for line in value.decode().split('\n'):
        line = line.replace('\r', '').replace(' ', '')
        if len(line.split(':')) > 1 or len(line.split('-')) > 1:
            pass
        else:
            dec += line.replace('\r', '')
    return base64.standard_b64decode(dec)


def encode_addr(addr):
    eaddr = []
    for i in addr:
        if i >= 0x80000000:
            i -= 0x80000000
            i = str(i) + "'"
        eaddr.append(i)
    return "m/" + "/".join(list(map(str, eaddr)))


if __name__ == '__main__':
    # Data
    version  = 0.2
    key_len  = 18
    kheader   = "Key:"
    aheader   = "Address:"

    # Code
    parser = argparse.ArgumentParser(description='Encrypt data with Trezor.')
    parser.add_argument("-n", "--address", help="the address to encrypt with")
    parser.add_argument("-k", "--key", help="the key to encrypt with")
    parser.add_argument("-s", "--secure", action="store_true", help="dont store key / address header")
    parser.add_argument("-d", "--decrypt", action="store_true", help="perform decryption operation")
    parser.add_argument("-v", "--verbose", action="store_true", help="high verbosity")
    args = parser.parse_args()
    device = get_transport()
    client = TrezorClient(transport=device, ui=ui.ClickUI())
    value = input_value(args)
    key, addr = input_key_addr(value, kheader, aheader, args)
    if args.verbose:
        sys.stderr.write(kheader + " " + str(key) + "\n" + aheader + " " + encode_addr(addr) + "\n")
    if args.decrypt:
        dec = misc.decrypt_keyvalue(client, addr, key, dearmor(value), ask_on_encrypt=False, ask_on_decrypt=False)
        sys.stdout.buffer.write(depad_value(dec))
    else:
        if len(value) > 1024:
            print("ERROR: Buffer exceeded max length of 1024")
            exit(-1)
        enc = misc.encrypt_keyvalue(client, addr, key, value, ask_on_encrypt=False, ask_on_decrypt=False)
        print('-----BEGIN TREZOR ENCRYPTED MESSAGE-----')
        print('Version:', 'trezor_encode', version, 'trezorlib', trezor_version, 'python', sys.version.split()[0])
        if not args.secure:
            print(kheader, key)
            print(aheader, encode_addr(addr))
        print('')
        print_enarmor(enc)
        print('-----END TREZOR ENCRYPTED MESSAGE-----')
    client.close()
