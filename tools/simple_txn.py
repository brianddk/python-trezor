#!/usr/bin/env python3

from trezorlib import btc, coins, messages as proto, tools, ui
from trezorlib.client import TrezorClient
from trezorlib.transport import get_transport

# self.setup_mnemonic_allallall() # see trezorlib///test_msg_signtx.py
# User Provided Fields; These are pulled from test scripts
# CHANGE THESE!!!
coin           = "Testnet"
in1_prev_hash  = "e5040e1bc1ae7667ffb9e5248e90b2fb93cd9150234151ce90e14ab2f5933bcd"
in1_prev_index = 0
in1_addr_path  = "44'/1'/0'/0/0"
in1_amount     = 31000000
out1_address   = "msj42CCGruhRsFrGATiUuh25dtxYtnpbTx"
out1_amount    = 30090000

# Defaults
sequence       = 4294967293

# Code
prev_hash=bytes.fromhex(in1_prev_hash)
device = get_transport()
client = TrezorClient(transport=device, ui=ui.ClickUI())

in1 = proto.TxInputType(
    address_n=tools.parse_path(in1_addr_path),
    prev_hash=prev_hash,
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

_, serialized_tx = btc.sign_tx(client, coin, [in1], [out1], prev_txes=coins.tx_api[coin])
client.close()
print('"txn_hex": {', serialized_tx.hex(), '}')
