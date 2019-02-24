#!/usr/bin/env python3
#
# Get in1_prev_txn_s from blockbook server.

from trezorlib import btc, coins, messages as proto, tools, ui
from trezorlib.client import TrezorClient
from trezorlib.transport import get_transport
from trezorlib.tx_api import json_to_tx
from json import loads
from decimal import Decimal

# self.setup_mnemonic_allallall() # see trezorlib///test_msg_signtx.py
# User Provided Fields; These are pulled from test scripts
# CHANGE THESE!!!
coin           = "Testnet"

# Get prev_txn hex from blockbook server.  For example:
# https://tbtc1.trezor.io/api/tx/37710bb2dedc40d28d149bad3c6fb19d263e0940f0512c3d5eb313337063e69d
in1_prev_txn_s = '{"txid":"37710bb2dedc40d28d149bad3c6fb19d263e0940f0512c3d5eb313337063e69d","version":2,"vin":[{"txid":"56b221de3d38dacfc99bf6fd0213a9bba90a6f2da80cd192e280a1593048eba1","vout":0,"sequence":4294967293,"n":0,"scriptSig":{"hex":"483045022100b80f2017a162d43ea026d000855f4e5440810843f0124cde5b05c2bc03a22a5002206f86baa17a70d7149571edd715b376f184153061ef4673a5a2072bab4cc874c00121033ea198bf5b768b32fe9c05071f0a01ad57194f2fbf13e2be175b327c354153f6"},"addresses":["myumog6JWYnCSPqatLCxpWwbs9YADXVHdY"],"value":"0.1"}],"vout":[{"value":"0.09999","n":0,"scriptPubKey":{"hex":"76a9144484481af74ff9496a41b571ca19bd627eee5d3088ac","addresses":["mmmEiBwbQZ7Q7wnS2UPz3e12YTSMfTzPBq"]},"spent":false}],"blockhash":"00000000db69a31a340c2f51f1d878074e75c0a2389ecee2a1031a37edb39f2f","blockheight":1446723,"confirmations":352,"blocktime":1544078884,"valueOut":"0.09999","valueIn":"0.1","fees":"0.00001","hex":"0200000001a1eb483059a180e292d10ca82d6f0aa9bba91302fdf69bc9cfda383dde21b256000000006b483045022100b80f2017a162d43ea026d000855f4e5440810843f0124cde5b05c2bc03a22a5002206f86baa17a70d7149571edd715b376f184153061ef4673a5a2072bab4cc874c00121033ea198bf5b768b32fe9c05071f0a01ad57194f2fbf13e2be175b327c354153f6fdffffff0198929800000000001976a9144484481af74ff9496a41b571ca19bd627eee5d3088ac00000000"}'

in1_prev_index = 0
in1_addr_path  = "44'/1'/0'/0/0"
in1_amount     = 9999000
out1_address   = "mmmEiBwbQZ7Q7wnS2UPz3e12YTSMfTzPBq"
out1_amount    = 9998000

# Defaults
tx_version     = 2
tx_locktime    = 0
sequence       = 4294967293

# Code
in1_prev_txn_j  = loads(in1_prev_txn_s, parse_float=Decimal)
in1_prev_hash   = in1_prev_txn_j['txid']
in1_prev_hash_b = bytes.fromhex(in1_prev_hash)
device = get_transport()
client = TrezorClient(transport=device, ui=ui.ClickUI())

txes = {}
signtx = proto.SignTx()

signtx.version = tx_version
signtx.lock_time = tx_locktime

in1 = proto.TxInputType(
    address_n=tools.parse_path(in1_addr_path),
    prev_hash=in1_prev_hash_b,
    prev_index=in1_prev_index,
    amount=in1_amount,
    script_type=proto.InputScriptType.SPENDADDRESS,
    sequence=sequence
)
out1 = proto.TxOutputType(
    address=out1_address,
    amount=out1_amount,
    script_type=proto.OutputScriptType.PAYTOADDRESS
)

txapi = coins.tx_api[coin]
tx = json_to_tx(coins.by_name[coin], in1_prev_txn_j)
txes[in1_prev_hash_b] = tx

_, serialized_tx = btc.sign_tx(client, coin, [in1], [out1], details=signtx, prev_txes=txes)
client.close()
print('"txn_hex": {', serialized_tx.hex(), '}')
