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
    # Refuse to build on a broken history: otherwise a new valid-looking block
    # could make a corrupted ledger appear to keep progressing.
    from ledger import validate_chain, validate_pending_transactions
    chain_errors = validate_chain(chain)
    if chain_errors:
        raise ValueError("cannot mine on an invalid chain: " + "; ".join(chain_errors))
    # Validate the whole pending sequence, so two queued payments cannot spend
    # the same confirmed output before either one is mined.
    errors = validate_pending_transactions(pending)
    if errors:
        raise ValueError("cannot mine invalid pending transactions: " + "; ".join(errors))
    reward = reward_transaction(account["address"])
    accepted = [reward.to_dict(), *pending]
    parent = chain[-1]["block_hash"] if chain else ""
    block = Block(len(chain), [item["tx_id"] for item in accepted], parent).mine()
    BlockChainDB().append(block.to_dict(), unique_key="block_hash")
    for transaction in accepted: TransactionDB().append(transaction, unique_key="tx_id")
    UnTransactionDB().clear()
    return block
