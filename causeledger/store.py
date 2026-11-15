"""SQLite transactions, optimistic locking and inspectable event snapshots."""
import hashlib
import json
import sqlite3
from pathlib import Path
from .domain import RuleError, apply, new_case, text, timestamp


class Conflict(RuleError):
    pass


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
                    at TEXT NOT NULL, actor TEXT NOT NULL, operation TEXT NOT NULL,
                    command TEXT NOT NULL, snapshot TEXT NOT NULL,
                    previous_hash TEXT NOT NULL, hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS no_event_update BEFORE UPDATE ON events
                BEGIN SELECT RAISE(ABORT, 'Events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS no_event_delete BEFORE DELETE ON events
                BEGIN SELECT RAISE(ABORT, 'Events are append-only'); END;
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def list(self):
        with self.connect() as db:
            return [json.loads(row['body']) for row in db.execute('SELECT body FROM cases ORDER BY rowid DESC')]

    def get(self, identity):
        with self.connect() as db:
            row = db.execute('SELECT body FROM cases WHERE id=?', (identity,)).fetchone()
            if row is None:
                raise KeyError(identity)
            return json.loads(row['body'])

    def history(self, identity):
        self.get(identity)
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM events WHERE case_id=? ORDER BY seq', (identity,))]

    def write(self, data, identity=None):
        if not isinstance(data, dict):
            raise RuleError('Request must be a JSON object')
        actor = text(data, 'actor', 200)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if identity:
                row = db.execute('SELECT body FROM cases WHERE id=?', (identity,)).fetchone()
                if row is None:
                    raise KeyError(identity)
                current = json.loads(row['body'])
                if type(data.get('version')) is not int or data['version'] != current['version']:
                    raise Conflict('Record changed. Reload and review before retrying.')
                case = apply(current, data)
            else:
                case = new_case(data)
            case['version'] += 1
            body = json.dumps(case, sort_keys=True)
            db.execute('INSERT OR REPLACE INTO cases VALUES (?,?)', (case['id'], body))
            previous = db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            previous_hash = previous['hash'] if previous else ''
            at = timestamp()
            operation = data.get('operation', 'create') if identity else 'create'
            command = json.dumps(data, sort_keys=True)
            digest = hashlib.sha256(json.dumps([previous_hash, case['id'], at, actor, operation, command, body]).encode()).hexdigest()
            db.execute('INSERT INTO events(case_id,at,actor,operation,command,snapshot,previous_hash,hash) VALUES (?,?,?,?,?,?,?,?)',
                       (case['id'], at, actor, operation, command, body, previous_hash, digest))
            return case

    def export(self):
        with self.connect() as db:
            # One transaction gives a consistent read snapshot.
            db.execute('BEGIN')
            cases = [json.loads(r['body']) for r in db.execute('SELECT body FROM cases ORDER BY rowid')]
            events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY seq')]
        return dict(format='causeledger-export', schema=1, exported_at=timestamp(), cases=cases, events=events)
