"""Local, dependency-free web UI for the Simple Blockchain Python demo.

The browser only renders data and sends button requests.  Every ledger action
is performed by the same account, transaction, miner, and validation modules
used by the command-line application.
"""
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from account import create_account, current_account
from explorer import block_summary
from ledger import ledger_report
from miner import mine_once
from transaction import Transaction

HOST, PORT = "127.0.0.1", 8000
ROOT = Path(__file__).parent


def application_state():
    """Return the read-only state displayed by the browser UI."""
    report = ledger_report()
    return {
        "account": current_account(),
        "ledger": report,
        "blocks": block_summary(),
        "instructions": {
            "account": "Create an account once, then mine a block to receive its reward.",
            "transfer": "Transfers use the current account and must spend confirmed UTXOs.",
        },
    }


class BlockchainUI(SimpleHTTPRequestHandler):
    """Serve the HTML page and a deliberately tiny JSON API on localhost."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        """Keep routine browser requests out of the teaching terminal."""

    def send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_payload(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ValueError("request body must be JSON") from error

    def do_GET(self):
        if self.path == "/api/state":
            self.send_json(application_state())
            return
        if self.path == "/":
            self.path = "/blockchain-explained.html"
        super().do_GET()

    def do_POST(self):
        try:
            payload = self.read_payload()
            if self.path == "/api/account":
                account = current_account()
                if account:
                    message = f"Using existing account {account['address']}."
                else:
                    _, account = create_account()
                    message = f"Created account {account['address']}. Mine a block to fund it."
            elif self.path == "/api/mine":
                block = mine_once()
                message = f"Mined block {block.height}: {block.block_hash[:16]}..."
            elif self.path == "/api/transfer":
                account = current_account()
                if not account:
                    raise RuntimeError("create an account before creating a transfer")
                recipient = str(payload.get("recipient", "")).strip()
                if not recipient:
                    raise ValueError("recipient is required")
                transaction = Transaction.transfer(account["address"], recipient, payload.get("amount"))
                message = f"Queued transaction {transaction.tx_id[:16]}... for mining."
            elif self.path == "/api/validate":
                report = ledger_report()
                message = "Ledger is valid." if report["valid"] else "; ".join(report["errors"])
            else:
                self.send_json({"error": "unknown API route"}, HTTPStatus.NOT_FOUND)
                return
            self.send_json({"message": message, "state": application_state()})
        except (RuntimeError, ValueError, TypeError) as error:
            self.send_json({"error": str(error), "state": application_state()}, HTTPStatus.BAD_REQUEST)


def serve(host=HOST, port=PORT):
    """Run the local UI server until interrupted with Ctrl+C."""
    server = ThreadingHTTPServer((host, int(port)), BlockchainUI)
    print(f"Open http://{host}:{port} in a browser. Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    serve()
