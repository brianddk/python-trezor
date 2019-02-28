#!/usr/bin/env python3
#
# Search wallet for bitcoin-like fork coins with activity and blockbook servers.
#   Doesn't do ADA, LSK, XMR, XEM, ONT, XLM, XTZ or any coin without blockbook.
# Increase max_accounts, max_addresses, for broader (and much slower) scans.

from trezorlib.client import TrezorClient
from trezorlib.transport import get_transport
from trezorlib.tools import parse_path
from trezorlib import btc, ethereum, messages
from trezorlib.ui import ClickUI
from os.path import isfile
import urllib.request
import json
import glob


def get_ethereum_address(path):
    transport = get_transport()
    ui = ClickUI()
    address = 'Error'
    try:
        client = TrezorClient(transport, ui)
        address = ethereum.get_address(client, parse_path(path))
    except Exception:
        pass
    finally:
        client.close()
    return address


def get_address(coin, path, addr_type):
    if addr_type == 'address':
        script_type = messages.InputScriptType.SPENDADDRESS
    if addr_type == 'p2shsegwit':
        script_type = messages.InputScriptType.SPENDP2SHWITNESS
    if addr_type == 'segwit':
        script_type = messages.InputScriptType.SPENDWITNESS
    transport = get_transport()
    ui = ClickUI()
    address = 'Error'
    try:
        client = TrezorClient(transport, ui)
        address = btc.get_address(client, coin['coin_name'], parse_path(path), show_display=False, multisig=None, script_type=script_type)
    except Exception:
        pass
    finally:
        client.close()
    return address


def get_path(coin, addr_type, account, change, index):
    if addr_type == 'address':
        path = "m/44'/" + str(coin['slip44']) + "'/" + str(account) + "'/" + str(change) + "/" + str(index)
    if addr_type == 'p2shsegwit':
        path = "m/49'/" + str(coin['slip44']) + "'/" + str(account) + "'/" + str(change) + "/" + str(index)
    if addr_type == 'segwit':
        path = "m/84'/" + str(coin['slip44']) + "'/" + str(account) + "'/" + str(change) + "/" + str(index)
    return path


def get_coins():
    coins = []
    files = ['../vendor/trezor-common/defs/ethereum/networks.json']

    for filename in glob.glob('../vendor/trezor-common/defs/bitcoin/*.json'):
        files.append(filename.replace('\\', '/'))

    # BCH-SV might be added here.
    # for filename in glob.glob('custom/*.json'):
        # files.append(filename.replace('\\', '/'))

    for file in files:
        if not isfile(file):
            print("ERROR:", file, "not found")
            print("       Don't forget to update submodues first!")
            print("       `git submodule update --init --remote`")
            exit(-1)
        with open(file) as json_data:
            coin = json.load(json_data)
            if type(coin) is dict:
                coin = [coin]
            for item in coin:
                if not item['blockbook']:
                    continue
                if ('chain_id' in item) and (item['slip44'] < 60):
                    continue
                if 'name' in item:
                    item['coin_name'] = item['name']
                    item['coin_label'] = item['name']

                # Use blocks like this to filter out known "alpha" coins
                # if item['coin_name'] == 'PIVX':
                    # continue

                if 'segwit' not in item:
                    item['segwit'] = False
                coins.append(item)
    return coins


def verify_coins(coins):
    verified = []

    for coin in coins:
        for url in coin['blockbook']:
            url += "/api/"
            q = urllib.request.Request(url)
            q.add_header('User-Agent', 'curl/7.55.1')
            try:
                with urllib.request.urlopen(q) as req:
                    data = req.read().decode()
                    if(data.replace(' ', '').find('"inSync":true') >= 0):
                        coin['api'] = url
                        break
            except Exception:
                pass

        if 'coin_label' in coin:
            label = coin['coin_label']
        else:
            label = coin['coin_name']
        if 'api' in coin:
            print("ADDING:", label)
            verified.append(coin)
        else:
            print("FAILED:", label)

    return verified


def get_address_info(coin, address):
    url = coin['api'] + 'address/' + address
    q = urllib.request.Request(url)
    q.add_header('User-Agent', 'curl/7.55.1')
    try:
        with urllib.request.urlopen(q) as req:
            data = json.loads(req.read().decode())
    except Exception:
        raise
    return data


def main():
    coins = get_coins()
    coins = verify_coins(coins)

    # max_accounts = 2
    # max_addresses = 4
    max_accounts = 1
    max_addresses = 1
    for coin in coins:
        account = -1
        blank_accounts = 0
        while(blank_accounts < max_accounts):
            account += 1
            blank_accounts += 1
            if coin['segwit']:
                types = ['address', 'p2shsegwit', 'segwit']
            else:
                types = ['address']
            for addr_type in types:
                index = -1
                blank_addresses = 0
                while (blank_addresses < max_addresses):
                    index += 1
                    blank_addresses += 1
                    for change in [0, 1]:
                        fmt_type = addr_type
                        # for fmt_type in types: # optional extra loop for fmt_type addr_type errors.
                        path = get_path(coin, addr_type, account, change, index)
                        # print(blank_accounts, blank_addresses, path, fmt_type)
                        if 'chain_id' in coin:
                            address = get_ethereum_address(path)
                        else:
                            address = get_address(coin, path, fmt_type)
                        try:
                            addr_info = get_address_info(coin, address)
                        except Exception:
                            print("ERROR:", coin['coin_label'], path, address)
                            addr_info = {'txApperances': 0}
                        if (('txApperances' in addr_info) and (addr_info['txApperances'] > 0)) or \
                                (('txs' in addr_info) and (addr_info['txs'] > 0)):
                            blank_accounts = blank_addresses = 0
                            print("ACTIVE:", coin['coin_label'], path, address)


if __name__ == '__main__':
    main()
