"""UTXO-style transactions and deterministic selection of spendable outputs."""
from __future__ import annotations

import hashlib
import time
from database import TransactionDB, UnTransactionDB
from model import Model


def digest(value) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


class Input(Model):
    def __init__(self, output_id, amount): self.output_id, self.amount = output_id, amount


class Output(Model):
    def __init__(self, recipient, amount):
        self.recipient, self.amount = recipient, amount
        self.output_id = digest((recipient, amount, time.time_ns()))


class Transaction(Model):
    def __init__(self, inputs, outputs):
        self.created_at = int(time.time())
        self.inputs = [item.to_dict() if isinstance(item, Model) else item for item in inputs]
        self.outputs = [item.to_dict() if isinstance(item, Model) else item for item in outputs]
        self.tx_id = digest((self.created_at, self.inputs, self.outputs))

    def to_dict(self): return self.__dict__

    @classmethod
    def transfer(cls, sender, recipient, amount):
        amount = int(amount)
        if amount <= 0:
            raise ValueError("transfer amount must be a positive whole number")
        chosen, change = select_outputs(unspent_outputs(sender), amount)
        if chosen is None:
            raise ValueError("insufficient confirmed funds")
        outputs = [Output(recipient, amount)]
        if change:
            outputs.append(Output(sender, change))
        transaction = cls([Input(item["output_id"], item["amount"]) for item in chosen], outputs)
        UnTransactionDB().append(transaction.to_dict(), unique_key="tx_id")
        return transaction


def unspent_outputs(address):
    records = TransactionDB().read()
    spent = {item["output_id"] for tx in records for item in tx["inputs"]}
    return [output for tx in records for output in tx["outputs"]
            if output["recipient"] == address and output["output_id"] not in spent]


def select_outputs(outputs, target):
    total, chosen = 0, []
    for output in sorted(outputs, key=lambda item: item["amount"]):
        chosen.append(output); total += output["amount"]
        if total >= target: return chosen, total - target
    return None, 0
