"""Loopback-only HTTP service. No runtime third-party dependencies."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .domain import RuleError, ready
from .store import Store, Conflict

STATIC = Path(__file__).parent / 'static'
MAX_BODY = 65536


def make_server(store, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Avoid writing case titles or request paths into server logs.

        def reply(self, status, body, mime='application/json'):
            raw = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(raw)

        def safe_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

        def do_GET(self):
            if not self.safe_host():
                return self.reply(403, {'error': 'Loopback Host required'})
            path = urlsplit(self.path).path
            try:
                if path == '/api/cases':
                    return self.reply(200, [{'case': c, 'gaps': ready(c)} for c in store.list()])
                if path == '/api/export':
                    return self.reply(200, store.export())
                if path.startswith('/api/cases/'):
                    identity = path.split('/')[3]
                    c = store.get(identity)
                    return self.reply(200, {'case': c, 'gaps': ready(c), 'history': store.history(identity)})
                files = {'/': ('index.html', 'text/html; charset=utf-8'),
                         '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                         '/style.css': ('style.css', 'text/css; charset=utf-8')}
                if path in files:
                    name, mime = files[path]
                    return self.reply(200, (STATIC / name).read_bytes(), mime)
                return self.reply(404, {'error': 'Not found'})
            except KeyError:
                self.reply(404, {'error': 'Case not found'})

        def do_POST(self):
            if not self.safe_host() or self.headers.get('Origin') not in {
                f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'
            }:
                return self.reply(403, {'error': 'Same-origin request required'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Use application/json'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BODY:
                    return self.reply(413, {'error': 'Request must be 1–65536 bytes'})
                data = json.loads(self.rfile.read(length))
                path = urlsplit(self.path).path
                if path == '/api/cases':
                    result = store.write(data)
                elif path.startswith('/api/cases/') and len(path.split('/')) == 4:
                    result = store.write(data, path.split('/')[3])
                else:
                    return self.reply(404, {'error': 'Not found'})
                self.reply(200, {'case': result, 'gaps': ready(result)})
            except Conflict as exc:
                self.reply(409, {'error': str(exc)})
            except (RuleError, ValueError, UnicodeDecodeError) as exc:
                self.reply(400, {'error': str(exc)})
            except KeyError:
                self.reply(404, {'error': 'Case not found'})
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description='Run CauseLedger on loopback only')
    parser.add_argument('--db', default='data/causeledger.sqlite3')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--demo', action='store_true', help='Seed fictional examples into an empty database')
    args = parser.parse_args()
    store = Store(args.db)
    if args.demo and not store.list():
        from .demo import seed
        seed(store)
    server = make_server(store, args.port)
    print(f'CauseLedger: http://127.0.0.1:{server.server_port} (single operator; local data)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
