"""Create reward transactions and commit pending transactions into a block."""
from __future__ import annotations

from account import current_account
from block import Block
from database import BlockChainDB, TransactionDB, UnTransactionDB
from transaction import Output, Transaction

BLOCK_REWARD = 20


def reward_transaction(address): return Transaction([], [Output(address, BLOCK_REWARD)])


def mine_once():
    account = current_account()
    if not account: raise RuntimeError("create an account before mining")
    chain, pending = BlockChainDB().read(), UnTransactionDB().read()
    reward = reward_transaction(account["address"])
    accepted = [reward.to_dict(), *pending]
    parent = chain[-1]["block_hash"] if chain else ""
    block = Block(len(chain), [item["tx_id"] for item in accepted], parent).mine()
    BlockChainDB().append(block.to_dict(), unique_key="block_hash")
    for transaction in accepted: TransactionDB().append(transaction, unique_key="tx_id")
    UnTransactionDB().clear()
    return block
