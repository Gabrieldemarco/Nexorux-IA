"""
Unit tests for core module.
"""
import os
import sqlite3
import tempfile

import pytest

from core import (
    DB_PATH,
    VERSION_PATH,
    bump_version,
    get_current_version,
    init_memory_db,
    load_conversations_from_db,
    load_messages_for_conversation,
    persist_message,
    append_message,
    persist_conversation,
    delete_conversation_from_db,
    rename_conversation_in_db,
    get_last_message_id,
)


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Redirect DB_PATH and VERSION_PATH to temp files for every test."""
    db = tmp_path / "nexorux_memory.sqlite3"
    ver = tmp_path / "version.json"
    monkeypatch.setattr("core.DB_PATH", db)
    monkeypatch.setattr("core.VERSION_PATH", ver)
    yield


def test_init_memory_db_creates_tables():
    init_memory_db()
    assert db_path().exists()
    with sqlite3.connect(db_path()) as conn:
        tables = [
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
    assert "conversations" in tables
    assert "messages" in tables


def test_persist_and_load_conversations():
    init_memory_db()
    persist_conversation("Chat 1")
    persisted = load_conversations_from_db()
    assert "Chat 1" in persisted
    assert persisted["Chat 1"] == []


def test_persist_message_and_append():
    init_memory_db()
    persist_conversation("C1")
    msg = {"role": "user", "content": "hola"}
    append_message("C1", msg)
    msgs = load_messages_for_conversation("C1")
    assert len(msgs) == 1
    assert msgs[0]["content"] == "hola"


def test_delete_conversation():
    init_memory_db()
    persist_conversation("ToDelete")
    append_message("ToDelete", {"role": "user", "content": "x"})
    delete_conversation_from_db("ToDelete")
    assert "ToDelete" not in load_conversations_from_db()


def test_bump_version_and_get_current_version():
    init_memory_db()
    assert get_current_version() == 0
    bump_version()
    assert get_current_version() == 1
    bump_version()
    assert get_current_version() == 2


def test_get_last_message_id():
    init_memory_db()
    persist_conversation("C2")
    assert get_last_message_id("C2") == 0
    append_message("C2", {"role": "assistant", "content": "uno"})
    assert get_last_message_id("C2") == 1
    append_message("C2", {"role": "user", "content": "dos"})
    assert get_last_message_id("C2") == 2


def test_rename_conversation_in_db():
    init_memory_db()
    persist_conversation("Old")
    append_message("Old", {"role": "user", "content": "hi"})
    rename_conversation_in_db("Old", "New")
    data = load_conversations_from_db()
    assert "New" in data
    assert "Old" not in data
    assert data["New"][0]["content"] == "hi"


def db_path():
    from core import DB_PATH
    return DB_PATH
