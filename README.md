# Simple Blockchain Python

Simple Blockchain Python is a compact, dependency-free blockchain learning project. It demonstrates accounts, UTXO transactions, proof-of-work blocks, JSON persistence, and simple XML-RPC communication.

It is deliberately **not** a cryptocurrency implementation. It omits signatures, validation, networking security, concurrency control, and a production consensus protocol.

## Run it

From this directory, use Python 3.10 or later:

```powershell
python console account create
python console miner start
python console blockchain list
python console ledger check
python console blockchain summary
```

After mining, transfer coins with:

```powershell
python console tx transfer SENDER_ADDRESS RECIPIENT_ADDRESS 5
python console miner start
```

Read [DESIGN.md](DESIGN.md) for the complete architecture and open `blockchain-explained.html` in a browser for an interactive visual walkthrough. It is an offline simulator: use its four stages to see rewards, UTXO spending, mining, and block links without changing your saved ledger.

`ledger check` prints the confirmed balances and explains any broken block,
transaction, or pending-payment rule it finds. It is a read-only inspection
tool, intended for experimenting with the JSON ledger files.

Use `python console address show ADDRESS` to follow one address's received,
spent, and pending-reservation events. It also separates confirmed funds from
funds that can immediately be used in another transfer. `blockchain summary`
shows each block's transaction identifiers and output volume.
