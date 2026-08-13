"""
Nexorux IA - Asistente Conversacional Local con streaming en vivo y voz
Main Streamlit application entry point.
Thin file that imports all functionality from modular components.
"""
import streamlit as st
from typing import Optional, List

# ── Importar desde módulos centrales ─────────────────────────────────
from core import (
    init_memory_db,
    load_conversations_from_db,
    persist_conversation,
    delete_conversation_from_db,
    append_message,
    get_current_version,
    load_messages_for_conversation,
    clear_messages_in_db,
)
from core.ollama_client import (
    get_models,
    default_model,
    model_supports_vision,
    call_ollama,
    call_ollama_stream,
    check_connection,
    get_active_backend,
    set_active_backend,
    BACKENDS,
)

# ── Importar desde módulos UI ────────────────────────────────────────
from ui.media import process_uploaded_file
from ui.chat_interface import initialize_chat_state, update_conversation_from_version
from ui.sidebar import _on_model_select, _set_active_conversation


# ===============================================================
# CSS PREMIUM
# ===============================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --nx-bg: #060608;
  --nx-bg-grad: radial-gradient(1200px 600px at 50% -10%, rgba(99,102,241,0.18), transparent 55%),
                radial-gradient(800px 400px at 80% 10%, rgba(34,211,238,0.12), transparent 55%),
                var(--nx-bg);
  --nx-surface: rgba(24,24,27,0.72);
  --nx-elevated: rgba(39,39,42,0.72);
  --nx-border: rgba(255,255,255,0.06);
  --nx-border-strong: rgba(255,255,255,0.1);
  --nx-text: #fafafa;
  --nx-muted: #a1a1aa;
  --nx-primary: #6366f1;
  --nx-primary-soft: rgba(99,102,241,0.14);
  --nx-accent: #22d3ee;
  --nx-danger: #ef4444;
  --nx-success: #22c55e;
  --nx-radius: 20px;
  --nx-shadow: 0 24px 60px rgba(0,0,0,0.55);
  --nx-glass: rgba(24,24,27,0.72);
  --nx-glass-border: rgba(255,255,255,0.07);
}

html, body, [data-testid="stApp"] {
  background: var(--nx-bg-grad) fixed !important;
  color: var(--nx-text) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  letter-spacing: -0.01em;
  text-rendering: optimizeLegibility;
}

.main .block-container {
  padding-bottom: 7rem;
  max-width: 980px;
  animation: nx-fade-in 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

[data-testid="stMain"] {
  background: transparent !important;
}

[data-testid="stSidebar"] {
  background: rgba(6,6,8,0.78) !important;
  border-right: 1px solid var(--nx-border) !important;
  backdrop-filter: blur(22px) saturate(1.6);
}

[data-testid="stSidebar"] * {
  color: var(--nx-text) !important;
  font-family: 'Inter', sans-serif !important;
}

/* Header */
.nexorux-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 6px 26px;
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(18px) saturate(1.35);
  background: rgba(6,6,8,0.45);
  border-bottom: 1px solid var(--nx-border);
}

.nexorux-brand {
  display: inline-flex;
  align-items: center;
  gap: 14px;
}

.nexorux-logo {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  background: linear-gradient(135deg, #6366f1, #22d3ee);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #000;
  font-weight: 800;
  font-size: 15px;
  box-shadow: 0 10px 28px rgba(99,102,241,0.4), inset 0 1px 0 rgba(255,255,255,0.35);
  letter-spacing: -0.02em;
}

.nexorux-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1.05;
  background: linear-gradient(to right, #fff, #e4e4e7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nexorux-subtitle {
  color: var(--nx-muted);
  font-size: 11px;
  margin-top: 3px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.nexorux-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--nx-glass);
  border: 1px solid var(--nx-glass-border);
  font-size: 11px;
  color: var(--nx-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
  backdrop-filter: blur(12px);
  transition: transform 0.18s ease, background 0.2s ease, border-color 0.2s ease;
}

.nexorux-pill:hover {
  transform: translateY(-1px);
  background: var(--nx-elevated);
  border-color: var(--nx-border-strong);
}

.nexorux-pill .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #52525b;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.45);
}
.nexorux-pill.ok .dot { background: var(--nx-success); box-shadow: 0 0 10px rgba(34,197,94,0.5); }
.nexorux-pill.bad .dot { background: var(--nx-danger); box-shadow: 0 0 10px rgba(239,68,68,0.5); }

/* Empty state */
.nexorux-empty {
  text-align: center;
  padding: 64px 16px 32px;
  color: var(--nx-muted);
  animation: nx-fade-in 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.nexorux-empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: saturate(1.2);
  animation: nx-float 3s ease-in-out infinite;
}

.nexorux-empty h3 {
  color: var(--nx-text);
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.02em;
}

.nexorux-empty p {
  margin: 10px 0 0;
  font-size: 14px;
  color: var(--nx-muted);
  line-height: 1.55;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}

/* Chat messages */
[data-testid="stChatMessage"] {
  background: var(--nx-surface) !important;
  border: 1px solid var(--nx-border);
  border-radius: var(--nx-radius);
  padding: 16px 18px !important;
  box-shadow: var(--nx-shadow);
  transition: transform 0.15s ease, box-shadow 0.25s ease, border-color 0.2s ease;
  backdrop-filter: blur(10px) saturate(1.15);
}

[data-testid="stChatMessage"]:hover {
  transform: translateY(-2px);
  box-shadow: 0 28px 56px rgba(0,0,0,0.6);
  border-color: var(--nx-border-strong);
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
  color: var(--nx-text) !important;
  font-size: 15px;
  line-height: 1.65;
  font-weight: 400;
}

/* Typing */
.nexorux-typing {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.65rem 1.1rem;
  color: var(--nx-muted);
  font-style: italic;
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.nexorux-typing .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #d4d4d8;
  box-shadow: 0 0 8px rgba(161,161,170,0.4);
  animation: nx-bounce 1.4s infinite ease-in-out both;
}

.nexorux-typing .dot:nth-child(1) { animation-delay: -0.32s; }
.nexorux-typing .dot:nth-child(2) { animation-delay: -0.16s; }
.nexorux-typing .dot:nth-child(3) { animation-delay: 0s; }

@keyframes nx-bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.35; }
  40% { transform: scale(1); opacity: 1; }
}

@keyframes nx-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}

/* TTS button */
.nexorux-tts-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  border: 1px solid var(--nx-border);
  border-radius: 999px;
  background: transparent;
  cursor: pointer;
  color: var(--nx-muted);
  margin-left: 10px;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  text-transform: uppercase;
}

.nexorux-tts-btn:hover {
  background: var(--nx-elevated);
  border-color: var(--nx-border-strong);
  color: var(--nx-text);
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(0,0,0,0.35);
}

.nexorux-tts-btn.speaking {
  background: rgba(34,197,94,0.14);
  border-color: var(--nx-success);
  color: #bbf7d0;
  box-shadow: 0 0 18px rgba(34,197,94,0.25);
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--nx-glass) !important;
  border: 1px dashed var(--nx-border-strong) !important;
  border-radius: var(--nx-radius) !important;
  backdrop-filter: blur(14px);
  transition: all 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
  border-color: var(--nx-primary) !important;
  background: rgba(39,39,42,0.7) !important;
  box-shadow: 0 0 0 4px var(--nx-primary-soft);
}

/* Chat input */
[data-testid="stChatInput"] {
  background: var(--nx-glass) !important;
  border: 1px solid var(--nx-glass-border) !important;
  border-radius: var(--nx-radius) !important;
  box-shadow: var(--nx-shadow);
  backdrop-filter: blur(16px) saturate(1.3);
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

[data-testid="stChatInput"]:focus-within {
  border-color: rgba(99,102,241,0.55) !important;
  box-shadow: 0 0 0 4px var(--nx-primary-soft), 0 24px 48px rgba(0,0,0,0.5);
}

[data-testid="stChatInput"] textarea {
  color: var(--nx-text) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
  line-height: 1.5 !important;
}

[data-testid="stChatInputSubmitButton"] {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  border-radius: 12px !important;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
  box-shadow: 0 8px 18px rgba(99,102,241,0.35);
}

[data-testid="stChatInputSubmitButton"]:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 10px 22px rgba(99,102,241,0.45);
}

/* Sidebar */
.nexorux-sidebar-section {
  background: var(--nx-glass);
  border: 1px solid var(--nx-glass-border);
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 12px;
  backdrop-filter: blur(14px) saturate(1.2);
  transition: background 0.2s ease, border-color 0.2s ease;
}

.nexorux-sidebar-section:hover {
  background: rgba(39,39,42,0.75);
  border-color: var(--nx-border-strong);
}

.nexorux-sidebar-title {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--nx-muted);
  margin-bottom: 12px;
  font-weight: 700;
}

.nexorux-divider {
  height: 1px;
  background: linear-gradient(to right, transparent, var(--nx-border-strong), transparent);
  margin: 18px 0;
}

.nexorux-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--nx-primary-soft);
  color: #c7d2fe;
  border: 1px solid rgba(99,102,241,0.3);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.08);
  border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.16);
}

@keyframes nx-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.nexorux-card {
  background: var(--nx-surface);
  border: 1px solid var(--nx-border);
  border-radius: var(--nx-radius);
  padding: 14px 16px;
  box-shadow: var(--nx-shadow);
  backdrop-filter: blur(10px);
}

[data-testid="stExpander"] {
  background: transparent !important;
  border: 1px solid var(--nx-border) !important;
  border-radius: 12px !important;
}

[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  letter-spacing: 0.02em;
}
</style>
"""


# ===============================================================
# FUNCIONES DE RENDERIZADO
# ===============================================================

def render_chat_message(message: dict, idx: int = 0) -> None:
    """Muestra un mensaje en el chat, con soporte para imágenes y botón TTS."""
    with st.chat_message(message["role"]):
        if message.get("image_b64"):
            import base64
            try:
                st.image(
                    base64.b64decode(message["image_b64"]),
                    caption=message.get("content") or "Imagen",
                    width='stretch',
                )
            except Exception:
                st.markdown(message.get("content", "Imagen"))
        elif "<img " in message.get("content", ""):
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("content"):
            content_clean = message["content"].replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('<', '<').replace('>', '>')
            html = (
                "<button class=\"nexorux-tts-btn\" onclick=\""
                "var synth = window.speechSynthesis;"
                "if (synth.speaking) { synth.cancel(); this.classList.remove('speaking'); return; }"
                "var u = new SpeechSynthesisUtterance('" + content_clean + "');"
                "u.lang = 'es-ES'; u.rate = 1.0;"
                "u.onend = function() { this.classList.remove('speaking'); }.bind(this);"
                "synth.speak(u); this.classList.add('speaking');"
                "\">Leer</button>"
            )
            st.markdown(html, unsafe_allow_html=True)


# ===============================================================
# HELPER: Llamada a Ollama con STREAMING (token por token)
# ===============================================================

def call_ollama_streaming_response(user_input: str, images: Optional[List[str]] = None) -> Optional[str]:
    """Envía mensaje al backend activo y renderiza tokens en vivo como ChatGPT."""
    backend = get_active_backend()
    model_to_use = st.session_state.get("active_model", default_model(backend))
    active = st.session_state.get("active_conversation", "Default")
    convo = st.session_state.get("conversations", {}).get(active, [])

    has_vision = model_supports_vision(model_to_use)

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

    full_text = ""
    message_placeholder = st.empty()

    try:
        for token in call_ollama_stream(
            user_input=user_input,
            model=model_to_use,
            conversation_history=history,
            images=images,
            backend=backend,
        ):
            if token.startswith("\n\n[Error:"):
                error_message = token
                message_placeholder.markdown(error_message)
                st.session_state["_last_api_error"] = error_message.strip()
                return None

            full_text += token
            message_placeholder.markdown(full_text + "▌")

        if not full_text.strip() and not st.session_state.get("_last_api_error"):
            message_placeholder.markdown("⚠️ La respuesta quedó vacía.")
            return None

        message_placeholder.markdown(full_text)

        if st.session_state.get("tts_response", False) and full_text.strip():
            clean = full_text.replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')
            st.html("<script>(function(){var synth=window.speechSynthesis;synth.cancel();var u=new SpeechSynthesisUtterance('" + clean + "');u.lang='es-ES';u.rate=1.0;synth.speak(u);})();</script>")

        st.session_state.pop("_last_api_error", None)
        return full_text.strip()

    except Exception as e:
        error_message = "Respuesta no disponible."
        message_placeholder.markdown(error_message)
        st.session_state["_last_api_error"] = error_message
        return None


def submit_chat_message(user_input: str, images: Optional[List[str]] = None) -> None:
    """Envía el mensaje del usuario, renderiza la respuesta y la guarda en el historial."""
    if not check_connection():
        st.error(
            "Ollama no está disponible. Iniciá `ollama serve` en otra terminal y recargá esta página."
        )
        return

    active = st.session_state.get("active_conversation", "Default")
    append_message(
        active,
        {
            "role": "user",
            "content": user_input,
            "model": st.session_state.get("active_model"),
        },
    )

    with st.chat_message("assistant"):
        full_response = call_ollama_streaming_response(user_input, images=images)

    if full_response:
        append_message(
            active,
            {
                "role": "assistant",
                "content": full_response,
                "model": st.session_state.get("active_model"),
            },
        )
    else:
        err = st.session_state.get("_last_api_error", "No se pudo generar una respuesta.")
        st.error(err)


def ensure_welcome_message(conversation_name: str) -> None:
    """Agrega un mensaje de bienvenida si la conversación está vacía."""
    convs = st.session_state.setdefault("conversations", {})
    msgs = convs.setdefault(conversation_name, [])
    if not msgs:
        append_message(
            conversation_name,
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
                "model": st.session_state.get("active_model"),
            },
        )


# ===============================================================
# CONFIGURACIÓN GLOBAL
# ===============================================================

WELCOME_MESSAGE = (
    "Hola, soy Nexorux IA, tu asistente local. "
    "Podes preguntarme cualquier cosa, subir archivos para que los lea o usar voz."
)

st.set_page_config(page_title="Nexorux IA", page_icon="⚡", layout="wide")

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

init_memory_db()
initialize_chat_state()
update_conversation_from_version()

# Inicializar configuración
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "auto_interpret" not in st.session_state:
    st.session_state["auto_interpret"] = True
if "model_select" not in st.session_state:
    st.session_state["model_select"] = st.session_state.get("active_model", default_model())
if "live_mode" not in st.session_state:
    st.session_state["live_mode"] = False
if "tts_response" not in st.session_state:
    st.session_state["tts_response"] = False

models = get_models(get_active_backend())
active_model = st.session_state.get("active_model")
if models and active_model not in models:
    st.session_state["active_model"] = models[0]

if st.session_state.get("model_select") != st.session_state.get("active_model"):
    if st.session_state.get("active_model") in models:
        st.session_state["model_select"] = st.session_state["active_model"]

# ===============================================================
# SIDEBAR
# ===============================================================

with st.sidebar:
    st.markdown('<div class="nexorux-brand"><div class="nexorux-logo">N</div><div><div class="nexorux-title">Nexorux IA</div><div class="nexorux-subtitle">Local · Privada · Offline</div></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="nexorux-sidebar-section"><div class="nexorux-sidebar-title">Backend</div>', unsafe_allow_html=True)
    backend_options = list(BACKENDS.keys())
    backend_labels = {b: BACKENDS[b]["label"] for b in backend_options}
    active_backend = get_active_backend()
    backend_index = backend_options.index(active_backend) if active_backend in backend_options else 0
    selected_backend = st.radio(
        "Motor local",
        backend_options,
        index=backend_index,
        format_func=lambda b: backend_labels[b],
        key="backend_select",
    )
    if selected_backend != active_backend:
        set_active_backend(selected_backend)
        st.cache_data.clear()
        st.session_state["model_select"] = default_model(selected_backend)
        st.session_state["active_model"] = st.session_state["model_select"]
        st.rerun()

    st.caption(f"Endpoint: {BACKENDS[selected_backend]['base_url']}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexorux-sidebar-section"><div class="nexorux-sidebar-title">Modelo</div>', unsafe_allow_html=True)
    if st.button("Recargar modelos", key="reload_models", use_container_width=True):
        st.cache_data.clear()
        backend = get_active_backend()
        models = get_models(backend)
        active = st.session_state.get("active_model")
        if models and active not in models:
            st.session_state["active_model"] = models[0]
        if st.session_state.get("active_model") in models:
            st.session_state["model_select"] = st.session_state["active_model"]
        st.rerun()

    st.selectbox(
        "Modelo de IA",
        get_models(get_active_backend()),
        key="model_select",
        on_change=_on_model_select,
        help="Para imágenes usá un modelo con visión: gemma4, llava, moondream...",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexorux-sidebar-section"><div class="nexorux-sidebar-title">Conversación</div>', unsafe_allow_html=True)
    convs = list(st.session_state.get("conversations", {}).keys()) or ["Default"]
    active_conv = st.session_state.get("active_conversation", "Default")
    idx = convs.index(active_conv) if active_conv in convs else 0

    st.selectbox(
        "Conversación activa",
        convs,
        index=idx,
        key="conversation_select",
        on_change=_set_active_conversation,
    )

    col_new, col_ren, col_del = st.columns([1, 1, 1])
    with col_new:
        if st.button("Nueva", use_container_width=True, key="new_chat_sidebar"):
            existing = list(st.session_state.get("conversations", {}).keys())
            i = 1
            name = f"Chat {i}"
            while name in existing:
                i += 1
                name = f"Chat {i}"
            st.session_state.setdefault("conversations", {})[name] = []
            persist_conversation(name)
            st.session_state["active_conversation"] = name
            st.rerun()

    with col_ren:
        if st.button("Renombrar", use_container_width=True, key="rename_chat_btn"):
            st.session_state["_renaming"] = True
            st.rerun()

    with col_del:
        if st.button("Eliminar", use_container_width=True, key="delete_chat_sidebar"):
            active = st.session_state.get("active_conversation", "Default")
            convs_dict = st.session_state.get("conversations", {})
            if active in convs_dict and len(convs_dict) > 1:
                del convs_dict[active]
                delete_conversation_from_db(active)
                st.session_state["active_conversation"] = list(convs_dict.keys())[0]
                st.rerun()
            elif active in convs_dict:
                st.warning("No podés eliminar la única conversación.")

    if st.button("Limpiar mensajes", use_container_width=True, key="clear_conversation"):
        active = st.session_state.get("active_conversation", "Default")
        if active != "Default":
            st.session_state["conversations"][active] = []
            clear_messages_in_db(active)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="nexorux-sidebar-section"><div class="nexorux-sidebar-title">Extras</div>', unsafe_allow_html=True)
    st.session_state["auto_interpret"] = st.checkbox(
        "Interpretar archivos automáticamente",
        value=st.session_state.get("auto_interpret", True),
        help="Al adjuntar un archivo, el modelo lo analiza y responde en el chat.",
    )
    st.session_state["live_mode"] = st.checkbox(
        "Modo conversación",
        value=st.session_state.get("live_mode", False),
        help="Al hablar por micrófono, el mensaje se envía automáticamente y la IA responde por voz",
    )
    st.session_state["tts_response"] = st.checkbox(
        "Respuesta por voz (TTS)",
        value=st.session_state.get("tts_response", False),
        help="La IA lee su respuesta en voz alta automáticamente",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Voz", expanded=False):
        st.text_input(
            "Nombre de voz (vacío = predeterminada)",
            value=st.session_state.get("tts_voice", ""),
            key="tts_voice",
            placeholder="ej: Helena, Pablo, Microsoft",
        )
        st.caption("Windows: Helena, Pablo · Chrome: Google español")

    st.markdown('<div class="nexorux-divider"></div>', unsafe_allow_html=True)
    active = st.session_state.get("active_conversation", "Default")
    msgs = st.session_state.get("conversations", {}).get(active, [])
    user_msgs = sum(1 for m in msgs if m.get("role") == "user")
    ass_msgs = sum(1 for m in msgs if m.get("role") == "assistant")
    st.caption(f"{user_msgs} mensajes tuyos · {ass_msgs} respuestas")

# ===============================================================
# ÁREA PRINCIPAL
# ===============================================================

active = st.session_state.get("active_conversation", "Default")
messages = st.session_state.get("conversations", {}).get(active, [])
model = st.session_state.get("active_model", default_model(get_active_backend()))
backend = get_active_backend()
connected = check_connection(backend)

st.markdown(
    f"""
    <div class="nexorux-header">
      <div class="nexorux-brand">
        <div class="nexorux-logo">N</div>
        <div>
          <div class="nexorux-title">Nexorux IA</div>
          <div class="nexorux-subtitle">{active} · {model} · {BACKENDS[backend]['label']}</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <div class="nexorux-pill {'ok' if connected else 'bad'}"><span class="dot"></span>{'Conectado' if connected else 'Desconectado'}</div>
        <div class="nexorux-pill">🧠 {model}</div>
        <div class="nexorux-pill">💬 {len(messages)}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not connected:
    st.error(f"{BACKENDS[backend]['label']} no está disponible. Iniciá el servicio en {BACKENDS[backend]['base_url']} y recargá esta página.")

# Validar estado del chat
if "conversations" not in st.session_state:
    st.session_state["conversations"] = load_conversations_from_db()
convs = st.session_state["conversations"]
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
            isinstance(msg, dict) and
            "role" in msg and msg["role"] in ["user", "assistant"] and
            "content" in msg and isinstance(msg["content"], str)
        ):
            valid_messages.append(msg)
    if len(valid_messages) != len(messages):
        st.info("ℹ️ Se corrigieron entradas de historial no válidas.")
        convs[active] = valid_messages

st.session_state["conversations"] = convs

# ── File uploader ──────────────────────────────────────────────────
uploaded_quick = st.file_uploader(
    "Adjuntar",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "gif", "webp", "txt", "md", "pdf", "csv", "json"],
    key="quick_upload",
)

all_uploads = list(uploaded_quick) if uploaded_quick else []
files_changed = False
if all_uploads:
    for f in all_uploads:
        name = getattr(f, "name", None)
        size = getattr(f, "size", None)
        fid = f"{name}:{size}" if name and size is not None else name
        if fid and fid in st.session_state["uploaded_files"]:
            continue
        process_uploaded_file(f)
        files_changed = True
        if fid:
            st.session_state["uploaded_files"].append(fid)

if files_changed:
    st.rerun()

# ── Renderizar historial existente ────────────────────────────────
act = st.session_state.get("active_conversation", "Default")
msgs = st.session_state.get("conversations", {}).get(act, [])
if not msgs:
    st.markdown(
        """
        <div class="nexorux-empty">
          <div class="nexorux-empty-icon">💡</div>
          <h3>Empecemos por algo sencillo</h3>
          <p>Escribí abajo, adjuntá un archivo o usá el micrófono.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    ensure_welcome_message(act)
    msgs = st.session_state.get("conversations", {}).get(act, [])
for i, m in enumerate(msgs):
    render_chat_message(m, i)

# ── Audio input nativo de Streamlit ──────────────────────────────
text_from_audio = ""
audio_input = st.audio_input("Grabar voz")
if audio_input is not None:
    audio_id = getattr(audio_input, "name", "unnamed")
    if st.session_state.get("_last_audio_id") != audio_id:
        try:
            import tempfile, os
            from faster_whisper import WhisperModel
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_input.read())
                    tmp_path = tmp.name
                with st.spinner("Transcribiendo..."):
                    model = WhisperModel("base", compute_type="int8", device="cpu")
                    segments, info = model.transcribe(tmp_path, language="es")
                    text_from_audio = " ".join(seg.text.strip() for seg in segments if seg.text)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            st.session_state["_last_audio_id"] = audio_id
            st.session_state["_pending_audio"] = text_from_audio
        except Exception as e:
            st.session_state["_last_audio_id"] = audio_id
            st.session_state["_pending_audio"] = ""
            st.warning(f"No se pudo transcribir el audio: {e}")
    else:
        text_from_audio = st.session_state.get("_pending_audio", "") or ""
else:
    st.session_state.pop("_last_audio_id", None)
    text_from_audio = st.session_state.get("_pending_audio", "") or ""

# ── Chat input ────────────────────────────────────────────────────
retry_prompt = st.session_state.pop("_retry_prompt", None)
user_prompt = ""

if text_from_audio:
    st.caption("Voz lista para enviar")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Enviar voz", key="send_audio_text"):
            user_prompt = text_from_audio
    with c2:
        if st.button("Descartar", key="discard_audio_text"):
            st.session_state["_pending_audio"] = ""
            st.rerun()

if retry_prompt:
    user_prompt = retry_prompt

if not user_prompt:
    user_prompt = st.chat_input("Escribe tu mensaje…", key="chat_input_main")

if user_prompt:
    if text_from_audio and user_prompt == text_from_audio:
        st.session_state["_pending_audio"] = ""
    submit_chat_message(user_prompt)

# ── Footer sutil ────────────────────────────────────────────────────
st.markdown(
    """
    <div style="
        margin-top: 28px;
        padding: 14px 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #71717a;
        font-size: 11px;
        letter-spacing: 0.06em;
        font-weight: 600;
        text-transform: uppercase;
        opacity: 0.85;
    ">
      <span>Nexorux IA</span>
      <span>Local · Privada · Offline</span>
    </div>
    """,
    unsafe_allow_html=True,
)