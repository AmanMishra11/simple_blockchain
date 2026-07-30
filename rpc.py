"""Minimal HTTP XML-RPC adapter for teaching node-to-node propagation."""
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer
from database import BlockChainDB, NodeDB, TransactionDB, UnTransactionDB


class LedgerRPC:
    def chain(self): return BlockChainDB().read()
    def transactions(self): return TransactionDB().read()
    def receive_block(self, block): return BlockChainDB().append(block, unique_key="block_hash")
    def receive_transaction(self, transaction): return UnTransactionDB().append(transaction, unique_key="tx_id")


def serve(host="127.0.0.1", port=3008):
    server = SimpleXMLRPCServer((host, int(port)), allow_none=True)
    server.register_instance(LedgerRPC()); server.serve_forever()


def broadcast(method, payload):
    for peer in NodeDB().read():
        try: getattr(ServerProxy(peer), method)(payload)
        except OSError: pass
