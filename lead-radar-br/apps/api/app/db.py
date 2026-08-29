from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from .config import DB_PATH


def connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = connect()
    conn.executescript(
        '''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS searches (
            id TEXT PRIMARY KEY,
            niche TEXT NOT NULL,
            location TEXT NOT NULL,
            radius_km REAL NOT NULL,
            depth TEXT NOT NULL,
            status TEXT NOT NULL,
            total_found INTEGER DEFAULT 0,
            qualified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            finished_at TEXT,
            error TEXT,
            settings_json TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            search_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            city TEXT,
            state TEXT,
            neighborhood TEXT,
            address TEXT,
            lat REAL,
            lon REAL,
            phone TEXT,
            email TEXT,
            website TEXT,
            cnpj TEXT,
            source_json TEXT DEFAULT '{}',
            social_json TEXT DEFAULT '{}',
            audit_json TEXT DEFAULT '{}',
            recommendation_json TEXT DEFAULT '{}',
            score INTEGER DEFAULT 0,
            funnel TEXT DEFAULT 'Topo',
            stage TEXT DEFAULT 'Novo',
            confidence INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(search_id, name, lat, lon),
            FOREIGN KEY(search_id) REFERENCES searches(id)
        );
        CREATE INDEX IF NOT EXISTS idx_leads_search_id ON leads(search_id);
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
        CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);
        '''
    )
    conn.commit()
    conn.close()


def _loads(value: Any, default: Any):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def row_to_search(row: sqlite3.Row | None):
    if not row:
        return None
    d = dict(row)
    d['settings'] = _loads(d.pop('settings_json', '{}'), {})
    return d


def row_to_lead(row: sqlite3.Row | None):
    if not row:
        return None
    d = dict(row)
    d['sources'] = _loads(d.pop('source_json', '{}'), {})
    d['social'] = _loads(d.pop('social_json', '{}'), {})
    d['audit'] = _loads(d.pop('audit_json', '{}'), {})
    d['recommendation'] = _loads(d.pop('recommendation_json', '{}'), {})
    return d
