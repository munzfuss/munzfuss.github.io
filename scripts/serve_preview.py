"""Local static preview server that forbids browser caching.

`python -m http.server` sends only Last-Modified, so browsers cache pages
heuristically and can show a stale copy after a rebuild — or a page from a
different site that was previously served on the same port. This server
adds `Cache-Control: no-store` to every response.

Usage: python scripts/serve_preview.py <port> <directory>
"""
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


def main() -> None:
    port, directory = int(sys.argv[1]), sys.argv[2]
    handler = functools.partial(NoCacheHandler, directory=directory)
    with ThreadingHTTPServer(("", port), handler) as httpd:
        print(f"Serving {directory} on http://localhost:{port}/ (no-store)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
