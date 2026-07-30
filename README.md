# Simple Blockchain Python

Simple Blockchain Python is a compact, dependency-free blockchain learning project. It demonstrates accounts, UTXO transactions, proof-of-work blocks, JSON persistence, and simple XML-RPC communication.

It is deliberately **not** a cryptocurrency implementation. It omits signatures, validation, networking security, concurrency control, and a production consensus protocol.

## Run it

From this directory, use Python 3.10 or later:

```powershell
python console account create
python console miner start
python console blockchain list
```

After mining, transfer coins with:

```powershell
python console tx transfer SENDER_ADDRESS RECIPIENT_ADDRESS 5
python console miner start
```

Read [DESIGN.md](DESIGN.md) for the complete architecture and open `blockchain-explained.html` in a browser for a small visual walkthrough.
