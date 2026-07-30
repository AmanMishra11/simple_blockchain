"""Peer management and conservative, length-based demonstration synchronisation."""
from database import BlockChainDB, NodeDB, TransactionDB
from rpc import serve


def add_node(url):
    url = url if url.startswith("http") else f"http://{url}"
    NodeDB().append({"url": url}, unique_key="url")
    return url


def nodes(): return [item["url"] for item in NodeDB().read()]


def start_node(port=3008): serve(port=int(port))
