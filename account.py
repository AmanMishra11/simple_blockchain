"""Toy wallet identities. Keys are illustrative, not production cryptography."""
from __future__ import annotations

import hashlib
import secrets
from database import AccountDB


def _address(public_key: str) -> str:
    return "L" + hashlib.sha256(public_key.encode()).hexdigest()[:33]


def create_account():
    private_key = secrets.token_hex(32)
    public_key = hashlib.sha256(private_key.encode()).hexdigest()
    account = {"address": _address(public_key), "public_key": public_key}
    AccountDB().append(account, unique_key="address")
    return private_key, account


def current_account():
    accounts = AccountDB().read()
    return accounts[0] if accounts else None
