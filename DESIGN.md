# Simple Blockchain design document

## Goal

Provide a readable, single-process demonstration of the core data flow behind a proof-of-work, UTXO-based blockchain. The code is structured as small modules so each concept can be studied independently.

## Components

| File | Responsibility |
| --- | --- |
| `account.py` | Generates a toy wallet identity and address. |
| `transaction.py` | Builds inputs and outputs, finds unspent outputs, and selects enough value for a payment. |
| `ledger.py` | Replays UTXOs and reports invalid transactions, blocks, and pending double-spends. |
| `explorer.py` | Builds read-only block and address views from the JSON ledger. |
| `block.py` | Defines a block header, calculates hashes, and searches for a valid nonce. |
| `miner.py` | Adds the 20-coin reward, collects the mempool, mines, and records the result. |
| `database.py` | Persists independent JSON lists for accounts, blocks, transactions, mempool, and peers. |
| `rpc.py` / `node.py` | Exposes a deliberately minimal XML-RPC transport and peer list. |
| `webapp.py` | Serves the local HTML UI and routes browser actions to the existing Python ledger modules. |
| `console` | Gives the project a small command-line interface. |

## Data model

An output owns an `amount`, a `recipient`, and a unique `output_id`. A later transaction spends it by placing its identifier and amount in an input. To calculate an address balance, the system examines all confirmed outputs belonging to the address and removes every output referenced by a confirmed input. Transfers require a positive whole-number amount, which prevents this small demo from creating nonsensical zero or negative outputs.

A transaction has a timestamp, input list, output list, and `tx_id`. Its identifier is a SHA-256 digest of those fields. When building a new transfer, outputs already referenced by a pending transfer are temporarily reserved, so an obvious double-spend is rejected immediately rather than waiting for mining. Blocks contain a height, timestamp, parent hash, and a list of transaction identifiers. This intentionally avoids a Merkle tree so the link between a block and its included transactions remains obvious.

## Mining sequence

1. A user creates an account.
2. The miner creates one 20-coin reward transaction for that account.
3. Pending transactions and the reward are collected.
4. The block header is hashed repeatedly with successive nonce values.
5. A hash beginning with four zeroes meets this demo's fixed difficulty.
6. The block and its confirmed transactions are written to disk; the mempool is cleared.

The parent hash makes a block depend on its predecessor. Changing an older block would change its hash and invalidate each descendant's reference.

## Ledger inspection

`python console ledger check` is a read-only teaching aid. It reconstructs the
UTXO set in transaction order, checks that each input references an available
output of the same value, and checks that non-reward transactions preserve
value. It also verifies block heights, parent links, proof of work, and that
each stored confirmed transaction is referenced by a block. Pending transfers
are replayed after the confirmed UTXOs, so a queued double-spend is reported
before the miner writes it to a block.

## Explorer views

The `blockchain summary` command maps each block to its included transactions,
reward/payment counts, and raw output volume. `address show ADDRESS` replays
the same records as a short history: received outputs, spent outputs, pending
incoming outputs, and outputs reserved by pending payments. It reports
confirmed, reserved, and spendable balances separately. This keeps the
important distinction between an owned UTXO and money that can be selected for
the next transfer visible without introducing a database or web interface.

## Local web application

`python webapp.py` starts a dependency-free server on `127.0.0.1:8000`.
The browser page contains only presentation code and HTTP requests; it never
creates blocks or balances itself. Its account, transfer, mining, and
validation routes call the same modules used by `console`, then return a fresh
ledger report and block summary. The UI therefore reflects the JSON ledger on
disk and persists its actions exactly like the command-line demo.

## Networking

Nodes may expose a small XML-RPC server and exchange a submitted block or pending transaction. This illustrates message propagation only. Peer discovery, authentication, retry handling, fork choice, and validation are outside the project scope.

## Deliberate limitations and next steps

- Private keys are not stored and there are no signatures: add elliptic-curve keys and signature verification.
- Transaction and block validation is not complete: verify inputs, values, hashes, reward limits, and parent links before storage.
- JSON files are not safe for simultaneous writers: use SQLite or an append-only log with file locking.
- The difficulty is fixed: add cumulative-work chain selection and periodic retargeting.
- XML-RPC peers are trusted: add authenticated P2P messages and a peer protocol.

These omissions keep the first version easy to trace while giving each later iteration a meaningful upgrade path.
