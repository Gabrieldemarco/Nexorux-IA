"""
Core module for Nexorux IA project.
Single source of truth for database operations, conversation management, and version tracking.
"""
import sqlite3
import json as _json
from pathlib import Path
from typing import Dict, List, Optional, Any

DB_PATH = Path(__file__).parent.with_name("nexorux_memory.sqlite3")
VERSION_PATH = Path(__file__).parent.with_name("version.json")


# ── VERSIÓN ──────────────────────────────────────────────────────────────

def bump_version() -> None:
    """Incrementa la versión para notificar a otros clientes."""
    try:
        with open(VERSION_PATH) as _f:
            v = _json.load(_f)
    except Exception:
        v = {"version": 0}
    v["version"] = v.get("version", 0) + 1
    with open(VERSION_PATH, "w") as _f:
        _json.dump(v, _f)


def get_current_version() -> int:
    """Retorna el número de versión actual."""
    try:
        with open(VERSION_PATH) as _f:
            return _json.load(_f).get("version", 0)
    except Exception:
        return 0


# ── BASE DE DATOS ────────────────────────────────────────────────────────

def init_memory_db() -> None:
    """Prepara la base local donde se guardan conversaciones y mensajes."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                name TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                image_b64 TEXT,
                model TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_name) REFERENCES conversations(name)
                    ON DELETE CASCADE
            )
            """
        )
        # Migración: agregar columna model si la tabla ya existía sin ella
        try:
            conn.execute("ALTER TABLE messages ADD COLUMN model TEXT")
        except sqlite3.OperationalError:
            pass  # ya existe
        count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        if count == 0:
            conn.execute("INSERT INTO conversations (name) VALUES ('Default')")


def load_conversations_from_db() -> Dict[str, List[Dict]]:
    """Carga conversaciones guardadas en SQLite con el formato que usa la UI."""
    init_memory_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.name, m.role, m.content, m.image_b64, m.model, m.created_at, c.created_at as conv_created_at
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_name = c.name
            ORDER BY c.created_at, m.id
            """
        ).fetchall()

    conversations = {}
    for row in rows:
        name = row["name"]
        conversations.setdefault(name, [])
        if row["role"] is None:
            continue
        message = {"role": row["role"], "content": row["content"]}
        if row["image_b64"]:
            message["image_b64"] = row["image_b64"]
        if row["model"]:
            message["model"] = row["model"]
        ts = row["created_at"]
        if ts:
            message["timestamp"] = ts
        conversations[name].append(message)

    return conversations or {"Default": []}


def get_last_message_id(name: str) -> int:
    """Retorna el max(id) de los mensajes de una conversación, 0 si no hay."""
    init_memory_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(id), 0) FROM messages WHERE conversation_name=?",
            (name,)
        ).fetchone()
        return row[0] if row else 0


def load_messages_for_conversation(name: str) -> List[Dict]:
    """Lee mensajes directo de SQLite para chat compartido (sin cache)."""
    init_memory_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, role, content, image_b64, model, created_at "
            "FROM messages WHERE conversation_name=? ORDER BY id",
            (name,)
        ).fetchall()
    result = []
    for r in rows:
        msg = {"role": r["role"], "content": r["content"], "id": r["id"]}
        if r["image_b64"]:
            msg["image_b64"] = r["image_b64"]
        if r["model"]:
            msg["model"] = r["model"]
        if r["created_at"]:
            msg["timestamp"] = r["created_at"]
        result.append(msg)
    return result


def persist_conversation(name: str) -> None:
    """Actualiza una conversación o la crea si no existe."""
    init_memory_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO conversations (name)
            VALUES (?)
            ON CONFLICT(name) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
            """,
            (name,),
        )


def delete_conversation_from_db(name: str) -> None:
    """Elimina una conversación y todos sus mensajes."""
    bump_version()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM messages WHERE conversation_name = ?", (name,))
        conn.execute("DELETE FROM conversations WHERE name = ?", (name,))


def persist_message(conversation_name: str, message: Dict) -> None:
    """Guarda un mensaje en la base de datos con su timestamp."""
    persist_conversation(conversation_name)
    bump_version()
    ts = message.get("timestamp")
    model = message.get("model")
    with sqlite3.connect(DB_PATH) as conn:
        if ts:
            conn.execute(
                """
                INSERT INTO messages (conversation_name, role, content, image_b64, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_name,
                    message["role"],
                    message["content"],
                    message.get("image_b64"),
                    model,
                    ts,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO messages (conversation_name, role, content, image_b64, model)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_name,
                    message["role"],
                    message["content"],
                    message.get("image_b64"),
                    model,
                ),
            )
        conn.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
            """,
            (conversation_name,),
        )


def clear_messages_in_db(conversation_name: str) -> None:
    """Borra todos los mensajes de una conversación sin eliminar la conversación misma."""
    init_memory_db()
    bump_version()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM messages WHERE conversation_name = ?", (conversation_name,))
        conn.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
            """,
            (conversation_name,),
        )

def rename_conversation_in_db(old_name: str, new_name: str) -> None:
    """Renombra una conversación y migra sus mensajes."""
    init_memory_db()
    bump_version()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN")
        try:
            conn.execute(
                "INSERT INTO conversations (name) VALUES (?)",
                (new_name,),
            )
            conn.execute(
                "UPDATE messages SET conversation_name = ? WHERE conversation_name = ?",
                (new_name, old_name),
            )
            conn.execute("DELETE FROM conversations WHERE name = ?", (old_name,))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise


# ── SESSION STATE HELPERS (Streamlit) ────────────────────────────────────

def append_message(conversation_name: str, message: Dict) -> None:
    """Añade un mensaje al chat en session_state y lo guarda en la base de datos."""
    import streamlit as st
    convs = st.session_state.setdefault("conversations", {})
    convs.setdefault(conversation_name, [])
    convs[conversation_name].append(message)
    persist_message(conversation_name, message)