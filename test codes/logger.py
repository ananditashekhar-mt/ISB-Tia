from datetime import datetime
import json
import sqlite3
import uuid

DB_PATH = "runtime.sqlite"


def init_db():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            started_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            intent TEXT,
            escalated INTEGER,
            reason TEXT,
            created_at TEXT
        );
    """)
  conn.commit()
  conn.close()


def save_message(session_id: str, role: str, content: str):
  init_db()
  conn = sqlite3.connect(DB_PATH)
  now = datetime.now().isoformat()

  conn.execute(
      """INSERT OR IGNORE INTO conversations VALUES (?, 'customer', ?, ?)""",
      (session_id, now, now),
  )
  conn.execute(
      """INSERT INTO messages VALUES (?, ?, ?, ?, ?)""",
      (str(uuid.uuid4()), session_id, role, content, now),
  )
  conn.commit()
  conn.close()


def log_audit(session_id: str, intent: str, escalated: bool, reason: str):
  init_db()
  conn = sqlite3.connect(DB_PATH)
  conn.execute(
      """INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)""",
      (
          str(uuid.uuid4()),
          session_id,
          intent,
          1 if escalated else 0,
          reason,
          datetime.now().isoformat(),
      ),
  )
  conn.commit()
  conn.close()


def get_chat_history(session_id: str):
  init_db()
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute(
      """SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at""",
      (session_id,),
  )
  rows = cursor.fetchall()
  conn.close()
  return [{"role": r[0], "content": r[1]} for r in rows]