#!/usr/bin/env python3
"""Serve the KSS decks and open a session's launcher page.

Run from anywhere (Linux, macOS, Windows):

    python3 docs/kss/_shared/serve.py            # session 1 launcher
    python3 docs/kss/_shared/serve.py 1 present  # session 1, presenter view
    python3 docs/kss/_shared/serve.py --no-open  # just serve

Runs in the foreground; Ctrl+C stops it. Binds to 127.0.0.1 only.

Over VS Code Remote-SSH, run it in the integrated terminal: VS Code spots the
printed http://localhost:PORT URL and forwards the port automatically, so
Ctrl+click on the URL works on your local machine. Outside an SSH session the
default browser is opened for you.
"""
import argparse
import functools
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # docs/kss
PAGES = {"index": "index.html", "present": "present.html", "show": "show.html"}


def find_session(arg: str) -> str:
    """Accept '1', '01', or a full/partial folder name."""
    sessions = sorted(p.name for p in ROOT.glob("session-*") if p.is_dir())
    if arg.isdigit():
        prefix = f"session-{int(arg):02d}-"
        matches = [s for s in sessions if s.startswith(prefix)]
    else:
        matches = [s for s in sessions if arg in s]
    if len(matches) != 1:
        sys.exit(f"Session '{arg}' not found or ambiguous. Available: {', '.join(sessions) or 'none'}")
    return matches[0]


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def bind(port: int, handler) -> Server:
    """Bind exactly this port. No silent fallback: a forwarded port must stay valid."""
    try:
        return Server(("127.0.0.1", port), handler)
    except OSError as e:
        sys.exit(f"Port {port} is unavailable ({e}). Stop the other server, or pass --port N.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?", default="1", help="session number or name (default: 1)")
    ap.add_argument("page", nargs="?", default="index", choices=PAGES, help="page to open (default: index)")
    ap.add_argument("--port", type=int, default=8000, help="port to serve on (default: 8000)")
    ap.add_argument("--no-open", action="store_true", help="do not open a browser")
    args = ap.parse_args()

    session = find_session(args.session)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):  # keep the terminal clean
            pass

    handler = functools.partial(Quiet, directory=str(ROOT))
    server = bind(args.port, handler)
    port = server.server_address[1]
    url = f"http://localhost:{port}/{session}/{PAGES[args.page]}"

    print(f"Serving {ROOT} on 127.0.0.1:{port}")
    print(f"  Launcher : http://localhost:{port}/{session}/index.html")
    print(f"  Presenter: http://localhost:{port}/{session}/present.html")
    print(f"  Audience : http://localhost:{port}/{session}/show.html")
    print("Ctrl+C to stop.")

    remote = any(os.environ.get(v) for v in ("SSH_CONNECTION", "SSH_TTY", "SSH_CLIENT"))
    if not args.no_open and not remote:
        webbrowser.open(url)
    elif remote:
        print("SSH session detected: Ctrl+click a URL above (VS Code forwards the port).")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
