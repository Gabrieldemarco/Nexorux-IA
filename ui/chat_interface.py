"""
Chat interface components for Streamlit frontend.
Handles conversation state, UI initialization, and main chat interface.
"""
import streamlit as st
from typing import List
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.with_name("nexorux_memory.sqlite3")

def set_up_page_config():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Asistente Privado Local",
        page_icon=":sparkles:",
        layout="wide",
    )

def initialize_chat_state():
    """Initialize or reset chat state with expected structure."""
    # Modelo Active
    if "active_model" not in st.session_state:
        from core.ollama_client import default_model
        st.session_state["active_model"] = default_model()

    # Inicializar estructura de conversaciones (permitir múltiples chats)
    if "conversations" not in st.session_state:
        from core import load_conversations_from_db
        st.session_state["conversations"] = load_conversations_from_db()

    active = st.session_state.get("active_conversation", "Default")
    convs = st.session_state.setdefault("conversations", {"Default": []})
    if active not in convs:
        convs[active] = []

    messages = convs[active]
    if not isinstance(messages, list):
        st.warning("⚠️ Estado de conversación corrupto. Reiniciando historial...")
        convs[active] = []
    else:
        valid_messages = []
        for msg in messages:
            if (
                isinstance(msg, dict)
                and "role" in msg
                and msg["role"] in ["user", "assistant"]
                and "content" in msg
                and isinstance(msg["content"], str)
            ):
                valid_messages.append(msg)
        if len(valid_messages) != len(messages):
            st.info("ℹ️ Se corrigieron entradas de historial no válidas.")
            convs[active] = valid_messages

    if "active_conversation" not in st.session_state:
        st.session_state["active_conversation"] = next(iter(st.session_state["conversations"]), "Default")

    # Configurar archivos
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    if "auto_interpret" not in st.session_state:
        st.session_state["auto_interpret"] = True
    if "model_select" not in st.session_state:
        st.session_state["model_select"] = st.session_state["active_model"]

def update_conversation_from_version():
    """Detect and load changes from other clients via version tracking."""
    from core import get_current_version, load_conversations_from_db

    try:
        _v = get_current_version()
        _old = st.session_state.get("_known_version", -1)
        if _old >= 0 and _v != _old:
            st.session_state["conversations"] = load_conversations_from_db()
        st.session_state["_known_version"] = _v
    except Exception:
        pass
