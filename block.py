"""Blocks link a set of transaction ids to their parent using proof of work."""
from __future__ import annotations

import hashlib
import time
from model import Model

POW_PREFIX = "0000"


class Block(Model):
    def __init__(self, height, transaction_ids, parent_hash=""):
        self.height, self.timestamp = height, int(time.time())
        self.transaction_ids, self.parent_hash = transaction_ids, parent_hash

    def header(self, nonce):
        return f"{self.height}|{self.timestamp}|{self.transaction_ids}|{self.parent_hash}|{nonce}"

    def hash_for(self, nonce): return hashlib.sha256(self.header(nonce).encode()).hexdigest()

    def mine(self):
        nonce = 0
        while not self.hash_for(nonce).startswith(POW_PREFIX): nonce += 1
        self.nonce, self.block_hash = nonce, self.hash_for(nonce)
        return self

    def valid(self):
        return hasattr(self, "nonce") and self.hash_for(self.nonce) == self.block_hash and self.block_hash.startswith(POW_PREFIX)
