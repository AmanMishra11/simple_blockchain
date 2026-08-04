"""Read-only ledger checks that make the demo's rules visible.

This module deliberately returns human-readable errors instead of raising while
walking the stored data.  That makes it useful both from the console and while
experimenting with deliberately broken JSON records.
"""
from __future__ import annotations

import hashlib

from block import POW_PREFIX
from database import BlockChainDB, TransactionDB, UnTransactionDB
from miner import BLOCK_REWARD
from transaction import digest


def _error(errors, message):
    errors.append(message)


def _is_positive_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def apply_transaction(transaction, available, allow_reward=False, known_output_ids=None):
    """Check one transaction and return errors while updating available UTXOs.

    `available` maps output ids to output records.  Updating it as each valid
    transaction is examined lets the caller demonstrate why a second spend of
    the same output is rejected.
    """
    errors = []
    if not isinstance(transaction, dict):
        return ["transaction is not an object"]

    tx_id = transaction.get("tx_id", "<unknown>")
    inputs, outputs = transaction.get("inputs"), transaction.get("outputs")
    if not isinstance(inputs, list) or not isinstance(outputs, list) or not outputs:
        return [f"transaction {tx_id}: inputs and a non-empty outputs list are required"]
    if not isinstance(transaction.get("created_at"), int):
        _error(errors, f"transaction {tx_id}: created_at must be an integer timestamp")
    elif tx_id != digest((transaction["created_at"], inputs, outputs)):
        _error(errors, f"transaction {tx_id}: identifier does not match its contents")

    output_total, output_ids = 0, set()
    new_outputs = []
    for index, output in enumerate(outputs):
        if not isinstance(output, dict) or not output.get("recipient"):
            _error(errors, f"transaction {tx_id}: output {index} needs a recipient")
            continue
        if not _is_positive_integer(output.get("amount")):
            _error(errors, f"transaction {tx_id}: output {index} has an invalid amount")
            continue
        output_id = output.get("output_id")
        if not output_id:
            _error(errors, f"transaction {tx_id}: output {index} needs an output_id")
            continue
        if output_id in output_ids:
            _error(errors, f"transaction {tx_id}: output {index} duplicates an output_id in this transaction")
            continue
        if known_output_ids is not None and output_id in known_output_ids:
            _error(errors, f"transaction {tx_id}: output {index} reuses an existing output_id")
            continue
        output_ids.add(output_id)
        output_total += output["amount"]
        new_outputs.append(output)

    if not inputs:
        if not allow_reward or output_total != BLOCK_REWARD or len(outputs) != 1:
            _error(errors, f"transaction {tx_id}: only a {BLOCK_REWARD}-coin reward may have no inputs")
    else:
        input_total, used_ids = 0, set()
        for index, item in enumerate(inputs):
            if not isinstance(item, dict) or not item.get("output_id"):
                _error(errors, f"transaction {tx_id}: input {index} needs an output_id")
                continue
            output_id = item["output_id"]
            if output_id in used_ids:
                _error(errors, f"transaction {tx_id}: input {index} spends an output twice")
                continue
            used_ids.add(output_id)
            referenced = available.get(output_id)
            if referenced is None:
                _error(errors, f"transaction {tx_id}: input {index} is already spent or unknown")
                continue
            if item.get("amount") != referenced["amount"]:
                _error(errors, f"transaction {tx_id}: input {index} amount does not match its output")
                continue
            input_total += referenced["amount"]
        if input_total != output_total:
            _error(errors, f"transaction {tx_id}: inputs ({input_total}) must equal outputs ({output_total})")

    if errors:
        return errors
    for item in inputs:
        available.pop(item["output_id"], None)
    for output in new_outputs:
        available[output["output_id"]] = output
    if known_output_ids is not None:
        known_output_ids.update(output_ids)
    return []


def confirmed_utxos(transactions=None):
    """Return the confirmed UTXO set and any transaction-validation errors."""
    available, errors, known_output_ids = {}, [], set()
    for transaction in transactions if transactions is not None else TransactionDB().read():
        errors.extend(apply_transaction(transaction, available, allow_reward=True,
                                        known_output_ids=known_output_ids))
    return available, errors


def validate_pending_transactions(pending=None, transactions=None):
    """Ensure pending payments are individually sound and do not double-spend."""
    transactions = TransactionDB().read() if transactions is None else transactions
    available, errors = confirmed_utxos(transactions)
    known_transaction_ids = {
        transaction.get("tx_id")
        for transaction in transactions if isinstance(transaction, dict)
        if transaction.get("tx_id")
    }
    known_output_ids = {
        output.get("output_id")
        for transaction in transactions if isinstance(transaction, dict)
        for output in transaction.get("outputs", []) if isinstance(output, dict)
        if output.get("output_id")
    }
    for transaction in pending if pending is not None else UnTransactionDB().read():
        tx_id = transaction.get("tx_id") if isinstance(transaction, dict) else None
        if tx_id and tx_id in known_transaction_ids:
            _error(errors, f"pending transaction {tx_id} duplicates an existing transaction")
        elif tx_id:
            known_transaction_ids.add(tx_id)
        errors.extend(apply_transaction(transaction, available, known_output_ids=known_output_ids))
    return errors


def _block_hash(block):
    header = f"{block['height']}|{block['timestamp']}|{block['transaction_ids']}|{block['parent_hash']}|{block['nonce']}"
    return hashlib.sha256(header.encode()).hexdigest()


def validate_chain(chain=None, transactions=None):
    """Return every structural, proof-of-work, and transaction error found."""
    chain = BlockChainDB().read() if chain is None else chain
    transactions = TransactionDB().read() if transactions is None else transactions
    errors, previous_hash, included = [], "", set()
    by_id, known_transaction_ids = {}, set()
    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue
        tx_id = transaction.get("tx_id")
        if tx_id in known_transaction_ids:
            _error(errors, f"transaction {tx_id}: identifier appears more than once")
            continue
        known_transaction_ids.add(tx_id)
        by_id[tx_id] = transaction

    for expected_height, block in enumerate(chain):
        if not isinstance(block, dict):
            _error(errors, f"block {expected_height}: not an object")
            continue
        if block.get("height") != expected_height:
            _error(errors, f"block {expected_height}: height is incorrect")
        if block.get("parent_hash") != previous_hash:
            _error(errors, f"block {expected_height}: parent hash does not link to its predecessor")
        required = {"height", "timestamp", "transaction_ids", "parent_hash", "nonce", "block_hash"}
        if not required.issubset(block) or not isinstance(block.get("transaction_ids"), list):
            _error(errors, f"block {expected_height}: required header fields are missing")
            continue
        calculated = _block_hash(block)
        if block["block_hash"] != calculated or not calculated.startswith(POW_PREFIX):
            _error(errors, f"block {expected_height}: proof of work is invalid")
        for tx_id in block["transaction_ids"]:
            if tx_id in included:
                _error(errors, f"block {expected_height}: transaction {tx_id} appears more than once")
            elif tx_id not in by_id:
                _error(errors, f"block {expected_height}: transaction {tx_id} is missing")
            included.add(tx_id)
        previous_hash = block.get("block_hash", previous_hash)

    _, transaction_errors = confirmed_utxos(transactions)
    errors.extend(transaction_errors)
    for tx_id in by_id:
        if tx_id not in included:
            _error(errors, f"transaction {tx_id} is not included in a block")
    return errors


def ledger_report():
    """Provide a small serialisable status report for the command-line demo."""
    chain, transactions, pending = BlockChainDB().read(), TransactionDB().read(), UnTransactionDB().read()
    chain_errors = validate_chain(chain, transactions)
    pending_errors = validate_pending_transactions(pending, transactions)
    available, _ = confirmed_utxos(transactions)
    balances = {}
    for output in available.values():
        balances[output["recipient"]] = balances.get(output["recipient"], 0) + output["amount"]
    return {
        "valid": not chain_errors and not pending_errors,
        "blocks": len(chain),
        "confirmed_transactions": len(transactions),
        "pending_transactions": len(pending),
        "balances": balances,
        "errors": chain_errors + pending_errors,
    }
