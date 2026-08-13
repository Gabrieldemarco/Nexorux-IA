"""
Ollama/LM Studio client integration for Streamlit UI.
Thin wrapper around core/ollama_client with Streamlit-specific caching.
"""
import streamlit as st
from typing import Optional, List

from core.ollama_client import (
    fetch_models as _fetch_models,
    call_ollama as _call_ollama,
    model_supports_vision as _model_supports_vision,
    vision_models_available as _vision_models_available,
    default_model as _default_model,
    check_connection as _check_connection,
    get_active_backend,
)


def _cache_key():
    backend = get_active_backend()
    return f"nx_cached_models_{backend}"


@st.cache_data(ttl=30, show_spinner=False)
def _cached_models(backend: str) -> List[str]:
    return _fetch_models(backend)


def available_models() -> List[str]:
    """Lista de modelos disponibles del backend activo, cacheada 30s."""
    try:
        return _cached_models(get_active_backend())
    except Exception:
        return []


def default_model() -> str:
    """Retorna el primer modelo disponible del backend activo o fallback."""
    backend = get_active_backend()
    models = available_models()
    return models[0] if models else _default_model(backend)


def ensure_active_model_valid() -> None:
    """Actualiza el modelo activo si el actual ya no está disponible."""
    models = available_models()
    active = st.session_state.get("active_model")
    if models and active not in models:
        st.session_state["active_model"] = models[0]


def model_supports_vision(model_name: str) -> bool:
    """Detecta si el modelo tiene soporte de visión."""
    return _model_supports_vision(model_name)


def _vision_models_available() -> List[str]:
    """Retorna una lista de modelos locales que tienen soporte de visión."""
    return _vision_models_available(available_models())


def bump_version() -> None:
    """Delegado a core."""
    from core import bump_version as _bump
    _bump()


def call_ollama_api(user_input: str, images: Optional[List[str]] = None) -> Optional[str]:
    """
    Envía el mensaje al backend activo con spinner de Streamlit.
    Mantiene compatibilidad con API existente.
    """
    backend = get_active_backend()
    model_to_use = st.session_state.get("active_model", default_model())
    active = st.session_state.get("active_conversation", "Default")
    convo = st.session_state.get("conversations", {}).get(active, [])

    has_vision = _model_supports_vision(model_to_use)

    if not images and has_vision:
        for msg in reversed(convo):
            if msg.get("role") == "user" and msg.get("image_b64"):
                images = [msg["image_b64"]]
                break

    if images and not has_vision:
        st.warning(
            f"⚠️ El modelo **{model_to_use}** no soporta imágenes. "
            "Cambiá a un modelo con visión como `gemma4`, `llava` o `moondream`."
        )
        return None

    history = []
    recent_convo = convo[-6:] if len(convo) > 6 else convo
    for msg in recent_convo:
        content = msg.get("content", "")
        if isinstance(content, str) and not content.startswith("[Archivo"):
            history.append({"role": msg["role"], "content": content})

    MAX_RETRIES = 4
    for attempt in range(MAX_RETRIES):
        try:
            spinner_text = f"⏳ (Intento {attempt + 1}/{MAX_RETRIES})"
            try:
                spinner_cm = st.spinner(spinner_text, help="El modelo local está pensando en tu respuesta.")
            except TypeError:
                spinner_cm = st.spinner(spinner_text)

            with spinner_cm:
                result = _call_ollama(
                    user_input=user_input,
                    model=model_to_use,
                    conversation_history=history,
                    images=images,
                    max_retries=1,
                    backend=backend,
                )
                if result:
                    return result

                st.session_state["_last_api_error"] = f"Error con modelo '{model_to_use}'"

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(2 * (2 ** attempt))
            else:
                st.session_state["_last_api_error"] = f"{type(e).__name__}: {e}"
                return None

    return None