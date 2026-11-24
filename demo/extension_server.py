"""
Local Python API bridge for the Chrome/Edge Extension.
Connects any live website in your browser directly to your real Python
affix-stripping and string-matching modules.
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "matching"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "affix"))

from naive import naive_search
from kmp import kmp_search
from boyer_moore import boyer_moore_search
from affix_stripper import strip_affix, load_known_roots

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "root_words.csv")
EXTENDED_DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "extended_dataset_experimental.csv")

KNOWN_ROOTS = load_known_roots(DATASET_PATH)
if os.path.exists(EXTENDED_DATASET_PATH):
    KNOWN_ROOTS.update(load_known_roots(EXTENDED_DATASET_PATH))

ALGORITHMS = {
    "naive": naive_search,
    "kmp": kmp_search,
    "boyer_moore": boyer_moore_search,
}


class ExtensionHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/analyze":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(body)

        raw_query = data.get("query", "").strip().lower()
        words = data.get("words", [])
        algo_key = data.get("algorithm", "naive")
        algo_func = ALGORITHMS.get(algo_key, naive_search)

        start = time.perf_counter()
        derived_root = strip_affix(raw_query, KNOWN_ROOTS) if raw_query else ""
        classifications = {}

        if raw_query:
            for word in words:
                w_lower = word.lower()
                plain_hit = bool(algo_func(raw_query, w_lower))
                word_root = strip_affix(w_lower, KNOWN_ROOTS)
                affix_hit = (
                    len(word_root) == len(derived_root)
                    and bool(algo_func(derived_root, word_root))
                )

                if plain_hit and affix_hit:
                    classifications[w_lower] = "both"
                elif affix_hit:
                    classifications[w_lower] = "affix_only"
                elif plain_hit:
                    classifications[w_lower] = "plain_only"

        elapsed_ms = (time.perf_counter() - start) * 1000

        response = {
            "raw_query": raw_query,
            "derived_root": derived_root,
            "classifications": classifications,
            "elapsed_ms": round(elapsed_ms, 4),
        }

        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        # Clean console output
        print(f"[Extension Server] {args[0]}")


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), ExtensionHandler)
    print(f"Loaded {len(KNOWN_ROOTS)} known Tagalog root words.")
    print("Affix-Aware Extension Server running at http://127.0.0.1:8765")
    print("Keep this terminal open while using the Chrome/Edge extension. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")