# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Build and open a local-only atlas server: uv run serve.py."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from build import build


if __name__ == "__main__":
    site = build()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), partial(SimpleHTTPRequestHandler, directory=str(site)))
    print("Lunar Atlas → http://127.0.0.1:8000  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
