"""
UI sidebar helpers for Nexorux IA.
Provides model selection and conversation change handlers.
"""
import streamlit as st


def _on_model_select():
    """Aplica directamente el modelo seleccionado en el sidebar."""
    sel = st.session_state.get("model_select")
    if sel:
        st.session_state["active_model"] = sel
        st.session_state["_pending_model"] = None
        st.session_state["_model_confirmed"] = False


def _set_active_conversation():
    sel = st.session_state.get("conversation_select")
    if sel and sel in st.session_state.get("conversations", {}):
        st.session_state["active_conversation"] = sel
        st.session_state["_pending_model"] = None
        st.session_state["_model_confirmed"] = False


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        pass
