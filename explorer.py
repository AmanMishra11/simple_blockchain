"""Read-only block and address views for following the ledger by hand.

The project stores simple JSON lists rather than an indexed database.  These
helpers turn those lists into small, serialisable views that show where a
payment lives and how an address balance changed over time.
"""
from __future__ import annotations

from database import BlockChainDB, TransactionDB, UnTransactionDB
from ledger import confirmed_utxos


def _records(chain=None, transactions=None, pending=None):
    """Load stores once, while allowing examples and tests to pass lists."""
    return (
        BlockChainDB().read() if chain is None else chain,
        TransactionDB().read() if transactions is None else transactions,
        UnTransactionDB().read() if pending is None else pending,
    )


def _transaction_index(transactions):
    return {
        item.get("tx_id"): item
        for item in transactions
        if isinstance(item, dict) and item.get("tx_id")
    }


def block_summary(chain=None, transactions=None):
    """Summarise each block without hiding its transaction identifiers.

    `output_volume` is the sum of non-reward outputs.  It intentionally counts
    change outputs too: that is a useful reminder that raw output volume is not
    the same as the value paid to another person.
    """
    chain, transactions, _ = _records(chain, transactions)
    by_id, summary = _transaction_index(transactions), []
    for position, block in enumerate(chain):
        if not isinstance(block, dict):
            summary.append({"position": position, "error": "block is not an object"})
            continue
        transaction_ids = block.get("transaction_ids", [])
        block_transactions = [by_id[item] for item in transaction_ids if item in by_id]
        rewards = [item for item in block_transactions if not item.get("inputs")]
        payments = [item for item in block_transactions if item.get("inputs")]
        output_volume = sum(
            output.get("amount", 0)
            for item in payments
            for output in item.get("outputs", [])
            if isinstance(output, dict) and isinstance(output.get("amount"), int)
        )
        summary.append({
            "height": block.get("height", position),
            "hash": block.get("block_hash", ""),
            "parent_hash": block.get("parent_hash", ""),
            "transactions": len(block_transactions),
            "rewards": len(rewards),
            "payments": len(payments),
            "output_volume": output_volume,
            "transaction_ids": transaction_ids,
        })
    return summary


def _block_locations(chain):
    locations = {}
    for position, block in enumerate(chain):
        if not isinstance(block, dict):
            continue
        for tx_id in block.get("transaction_ids", []):
            locations[tx_id] = block.get("height", position)
    return locations


def address_history(address, chain=None, transactions=None, pending=None):
    """Return incoming and outgoing records for one address in ledger order."""
    chain, transactions, pending = _records(chain, transactions, pending)
    locations, produced, events = _block_locations(chain), {}, []
    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue
        tx_id, height = transaction.get("tx_id", "<unknown>"), locations.get(transaction.get("tx_id"))
        for output in transaction.get("outputs", []):
            if isinstance(output, dict) and output.get("output_id"):
                produced[output["output_id"]] = output
            if isinstance(output, dict) and output.get("recipient") == address:
                events.append({
                    "state": "confirmed", "direction": "received", "block": height,
                    "tx_id": tx_id, "amount": output.get("amount"), "output_id": output.get("output_id"),
                })
        for item in transaction.get("inputs", []):
            referenced = produced.get(item.get("output_id")) if isinstance(item, dict) else None
            if referenced and referenced.get("recipient") == address:
                events.append({
                    "state": "confirmed", "direction": "spent", "block": height,
                    "tx_id": tx_id, "amount": referenced.get("amount"), "output_id": item.get("output_id"),
                })
    for transaction in pending:
        if not isinstance(transaction, dict):
            continue
        tx_id = transaction.get("tx_id", "<unknown>")
        for output in transaction.get("outputs", []):
            if isinstance(output, dict) and output.get("recipient") == address:
                events.append({
                    "state": "pending", "direction": "receives", "block": None,
                    "tx_id": tx_id, "amount": output.get("amount"), "output_id": output.get("output_id"),
                })
        for item in transaction.get("inputs", []):
            referenced = produced.get(item.get("output_id")) if isinstance(item, dict) else None
            if referenced and referenced.get("recipient") == address:
                events.append({
                    "state": "pending", "direction": "reserves", "block": None,
                    "tx_id": tx_id, "amount": referenced.get("amount"), "output_id": item.get("output_id"),
                })
    return events


def address_summary(address, chain=None, transactions=None, pending=None):
    """Show confirmed, reserved, and immediately spendable value separately."""
    chain, transactions, pending = _records(chain, transactions, pending)
    available, errors = confirmed_utxos(transactions)
    confirmed = sum(item["amount"] for item in available.values() if item.get("recipient") == address)
    reserved_ids = {
        item.get("output_id")
        for transaction in pending
        if isinstance(transaction, dict)
        for item in transaction.get("inputs", [])
        if isinstance(item, dict)
    }
    reserved = sum(
        item["amount"] for output_id, item in available.items()
        if item.get("recipient") == address and output_id in reserved_ids
    )
    return {
        "address": address,
        "confirmed_balance": confirmed,
        "reserved_by_pending": reserved,
        "spendable_balance": confirmed - reserved,
        "history": address_history(address, chain=chain, transactions=transactions, pending=pending),
        "ledger_errors": errors,
    }
