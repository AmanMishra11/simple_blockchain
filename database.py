"""Append-only JSON stores used by the educational ledger."""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).with_name("data")


class JsonStore:
    filename = ""

    @property
    def path(self):
        return DATA_DIR / self.filename

    def read(self):
        if not self.path.exists() or not self.path.read_text(encoding="utf-8").strip():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def replace(self, records):
        DATA_DIR.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def append(self, record, unique_key=None):
        records = self.read()
        if unique_key and any(item.get(unique_key) == record.get(unique_key) for item in records):
            return False
        records.append(record)
        self.replace(records)
        return True

    def clear(self):
        self.replace([])


class AccountDB(JsonStore): filename = "accounts.json"
class BlockChainDB(JsonStore): filename = "blockchain.json"
class TransactionDB(JsonStore): filename = "transactions.json"
class UnTransactionDB(JsonStore): filename = "mempool.json"
class NodeDB(JsonStore): filename = "nodes.json"
