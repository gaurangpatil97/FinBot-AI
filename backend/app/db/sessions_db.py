import sqlite3
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.models.schemas import Citation

DB_PATH = Path(__file__).parent.parent.parent / "sessions.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        company_slug TEXT NOT NULL,
        title TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        citations TEXT,
        routing_debug TEXT,
        latency REAL,
        created_at TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    )
    """)
    
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN chunks TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

def create_session(company_slug: str, title: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    if not title:
        title = "New Chat"
        
    cursor.execute(
        "INSERT INTO sessions (id, company_slug, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, company_slug, title, now, now)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def list_sessions(company_slug: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE company_slug = ? ORDER BY updated_at DESC", (company_slug,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_message(session_id: str, role: str, content: str, citations: List[Any], routing_debug: Dict[str, Any], latency: float, chunks: List[Any] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    citations_json = json.dumps([c.model_dump() if hasattr(c, "model_dump") else c for c in citations]) if citations else "[]"
    routing_debug_json = json.dumps(routing_debug) if routing_debug else "{}"
    chunks_json = json.dumps(chunks) if chunks else "[]"
    
    cursor.execute(
        "INSERT INTO messages (id, session_id, role, content, citations, routing_debug, latency, chunks, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (msg_id, session_id, role, content, citations_json, routing_debug_json, latency, chunks_json, now)
    )
    
    cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_messages(session_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        d["citations"] = json.loads(d["citations"]) if d["citations"] else []
        d["routing_debug"] = json.loads(d["routing_debug"]) if d["routing_debug"] else {}
        d["chunks"] = json.loads(d["chunks"]) if ("chunks" in d and d["chunks"]) else []
        results.append(d)
        
    return results

def delete_session(session_id: str) -> bool:
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def rename_session(session_id: str, new_title: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (new_title, now, session_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated
