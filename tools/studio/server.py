#!/usr/bin/env python3
"""Loopback Studio API and static application server."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from model import StudioError, valid_id, find
from store import Store, MAX_UPLOAD
from jobs import create_job, review_job, inbox
from boards import create_storyboard, review_storyboard


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store, web_root=None):
        self.store = store
        self.web_root = Path(web_root or Path(__file__).parent / "web").resolve()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "PinPinStudio/1"

    def log_message(self, fmt, *args):
        # Never log POST bodies, prompts, uploaded bytes, or local credentials.
        print(self.log_date_time_string(), fmt % args, flush=True)

    def _guard(self, mutation=False):
        host = urlsplit("http://" + self.headers.get("Host", ""))
        if host.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise StudioError("Studio is available on loopback only", "origin_forbidden", 403)
        origin = self.headers.get("Origin")
        if mutation and origin:
            parsed = urlsplit(origin)
            if parsed.scheme not in ("http", "https") or parsed.netloc != host.netloc:
                raise StudioError("Cross-origin mutations are blocked", "origin_forbidden", 403)

    def _json(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _file(self, path, mime, etag=None):
        if etag and self.headers.get("If-None-Match") == '"' + etag + '"':
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "private, max-age=31536000, immutable" if etag else "no-cache")
        if etag:
            self.send_header("ETag", '"' + etag + '"')
        self.end_headers()
        if self.command != "HEAD":
            with path.open("rb") as stream:
                while chunk := stream.read(256 * 1024):
                    self.wfile.write(chunk)

    def _body(self, maximum=8 * 1024 * 1024, json_body=True):
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError as exc:
            raise StudioError("Invalid Content-Length") from exc
        if length < 0:
            raise StudioError("Content-Length required")
        if length > maximum:
            raise StudioError("Request body is too large", "upload_size", 413)
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise StudioError("Incomplete request body")
        if not json_body:
            return raw
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise StudioError("Use application/json", "content_type", 415)
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise StudioError("Invalid JSON") from exc
        if not isinstance(body, dict):
            raise StudioError("JSON body must be an object")
        return body

    def _route(self, method):
        self._guard(method in ("POST", "PUT"))
        path = unquote(urlsplit(self.path).path)
        if "\x00" in path or "\\" in path or any(p in (".", "..") for p in path.split("/")):
            raise StudioError("Invalid path", "path_forbidden", 403)
        store = self.server.store
        if method == "GET":
            if path == "/api/state":
                return self._json(200, store.read())
            if path == "/api/jobs":
                state = store.read()
                return self._json(200, {"jobs": state["jobs"], "revision": state["revision"]})
            if path == "/api/inbox":
                return self._json(200, inbox(store))
            if path == "/api/history":
                return self._json(200, {"revisions": store.project_history()})
            if path.startswith("/api/history/"):
                revision = path.removeprefix("/api/history/")
                if not revision.isdigit():
                    raise StudioError("Invalid revision")
                return self._json(200, store.project_revision(int(revision)))
            if path.startswith("/api/assets/"):
                identifier = valid_id(path.removeprefix("/api/assets/"), "asset id")
                state = store.read()
                asset = find(state["assets"], identifier, "asset")
                return self._file(store.asset_path(identifier, state), asset["mime"], asset["sha256"])
            if path.startswith("/api/"):
                raise StudioError("Route not found", "not_found", 404)
            file = (self.server.web_root / (path.lstrip("/") or "index.html")).resolve()
            if not file.is_relative_to(self.server.web_root) or not file.is_file():
                raise StudioError("Page not found", "not_found", 404)
            return self._file(file, mimetypes.guess_type(file)[0] or "application/octet-stream")
        if method == "PUT" and path == "/api/state":
            body = self._body()
            return self._json(200, store.save_project(body.get("project"), body.get("expectedRevision")))
        if method == "POST":
            if path == "/api/assets":
                name = unquote(self.headers.get("X-File-Name", "image"))
                asset, state = store.upload_asset(self._body(MAX_UPLOAD, False), name)
                return self._json(201, {"asset": asset, "revision": state["revision"]})
            body = self._body()
            if path == "/api/jobs":
                job, state = create_job(store, body)
                return self._json(201, {"job": job, "revision": state["revision"]})
            if path == "/api/storyboards":
                board, state = create_storyboard(store, body)
                return self._json(201, {"storyboard": board, "revision": state["revision"]})
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[0] == "api" and parts[3] == "review":
                identifier = valid_id(parts[2])
                if parts[1] == "jobs":
                    result, state = review_job(store, identifier, body)
                    return self._json(200, {"job": result, "revision": state["revision"]})
                if parts[1] == "storyboards":
                    result, state = review_storyboard(store, identifier, body)
                    return self._json(200, {"storyboard": result, "revision": state["revision"]})
        raise StudioError("Route not found", "not_found", 404)

    def dispatch(self, method):
        try:
            self._route(method)
        except StudioError as exc:
            self._json(exc.status, exc.payload())
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            # Generic response avoids leaking local paths or environment through tracebacks.
            import traceback
            traceback.print_exc()
            self._json(500, {"error": {"code": "internal_error", "message": "Studio request failed; inspect server log"}})

    def do_GET(self):
        self.dispatch("GET")

    def do_HEAD(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PUT(self):
        self.dispatch("PUT")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--media-root", action="append", default=[])
    parser.add_argument("--port", type=int, default=18806)
    args = parser.parse_args()
    store = Store(args.data_dir, args.media_root)
    server = StudioServer(("127.0.0.1", args.port), store)
    print("Studio listening on http://127.0.0.1:" + str(args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
