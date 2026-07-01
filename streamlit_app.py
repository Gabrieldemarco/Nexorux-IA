import streamlit as st
from dotenv import load_dotenv
import sqlite3
import requests
import time
from typing import Optional, List
from pathlib import Path

# ===============================================================
# CONFIGURACIÓN GLOBAL Y VERIFICACIÓN DE OLLAMA (0 ASUMIMIENTOS)
# ===============================================================
load_dotenv()

DB_PATH = Path(__file__).with_name("vora_memory.sqlite3")


def init_memory_db() -> None:
    """Prepara la base local donde se guardan conversaciones y mensajes."""
    with sqlite3.connect(DB_PATH) as conn:
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(conversation_name) REFERENCES conversations(name)
                    ON DELETE CASCADE
            )
            """
        )
        conn.execute("INSERT OR IGNORE INTO conversations (name) VALUES ('Default')")


def load_conversations_from_db() -> dict:
    """Carga conversaciones guardadas en SQLite con el formato que usa la UI."""
    init_memory_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.name, m.role, m.content, m.image_b64
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
        conversations[name].append(message)

    return conversations or {"Default": []}


def persist_conversation(name: str) -> None:
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
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM messages WHERE conversation_name = ?", (name,))
        conn.execute("DELETE FROM conversations WHERE name = ?", (name,))


def persist_message(conversation_name: str, message: dict) -> None:
    persist_conversation(conversation_name)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO messages (conversation_name, role, content, image_b64)
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_name,
                message["role"],
                message["content"],
                message.get("image_b64"),
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


def append_message(conversation_name: str, message: dict) -> None:
    convs = st.session_state.setdefault("conversations", {})
    convs.setdefault(conversation_name, [])
    convs[conversation_name].append(message)
    persist_message(conversation_name, message)


st.set_page_config(page_title="Asistente Privado Local", page_icon=":sparkles:", layout="wide")

# --- VERIFICAMOS QUE OLLAMA ESTÉ CORRIENDO Y OBTENEMOS MODELOS DISPONIBLES ---
@st.cache_data(ttl=60)
def get_available_ollama_models() -> List[str]:
    """Consulta tu instancia local de Ollama para listar modelos disponibles (robusto ante distintos endpoints/responses)."""
    endpoints = [
        "http://localhost:11434/api/models",
        "http://localhost:11434/api/tags",
        "http://localhost:11434/api/list_models",
    ]
    for url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Varias formas posibles de recibir modelos: dict{'models': [...]}, list[...] o dict lista plana
            models = []
            if isinstance(data, dict):
                if "models" in data and isinstance(data["models"], list):
                    items = data["models"]
                else:
                    # Algunas APIs devuelven un dict con keys dinámicas
                    # Intentamos tomar una lista si aparece
                    items = []
                    for v in data.values():
                        if isinstance(v, list):
                            items = v
                            break
            elif isinstance(data, list):
                items = data
            else:
                items = []

            for m in items:
                if isinstance(m, dict):
                    name = m.get("name") or m.get("id") or m.get("model")
                    if name:
                        models.append(str(name))
                else:
                    models.append(str(m))

            if models:
                return models

        except requests.exceptions.ConnectionError:
            # Intencional: probamos siguientes endpoints antes de fallar
            continue
        except Exception:
            # Ignoramos y probamos siguiente endpoint
            continue

    st.error("🚨 ¡ERROR DE CONEXIÓN! No se puede conectar a Ollama en http://localhost:11434.\n"
             "Por favor, asegúrate de tener Ollama ejecutándose (ejecuta `ollama serve` en una terminal).")
    st.stop()


def available_models() -> List[str]:
    """Lista actualizada de modelos (respeta caché y recargas)."""
    return get_available_ollama_models()


def default_model() -> str:
    models = available_models()
    return models[0] if models else "llama3:latest"


def ensure_active_model_valid() -> None:
    models = available_models()
    active = st.session_state.get("active_model")
    if models and active not in models:
        st.session_state["active_model"] = models[0]


# Inicializamos el modelo activo en session_state para permitir cambios desde la UI
if "active_model" not in st.session_state:
    st.session_state["active_model"] = default_model()
else:
    ensure_active_model_valid()

# Inicializar estructura de conversaciones (permitir múltiples chats)
if "conversations" not in st.session_state:
    st.session_state["conversations"] = load_conversations_from_db()
if "active_conversation" not in st.session_state:
    st.session_state["active_conversation"] = next(iter(st.session_state["conversations"]), "Default")

# Inicializar configuración de archivos
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []
if "auto_interpret" not in st.session_state:
    st.session_state["auto_interpret"] = True
if "model_select" not in st.session_state:
    st.session_state["model_select"] = st.session_state["active_model"]

# Función para detectar si el modelo soporta visión
def model_supports_vision(model_name: str) -> bool:
    """Detecta si el modelo de Ollama tiene soporte de visión."""
    vision_models = [
        "llava", "bakllava", "moondream", "minicpm-v", "phi3-vision",
        "llama3.2-vision", "gemma3", "gemma3:4b", "gemma-3", "gemma4", "gemma4:latest", "qwen2-vl", "qwen-vl",
    ]
    model_lower = model_name.lower()
    return any(vision in model_lower for vision in vision_models)

def _set_active_conversation():
    sel = st.session_state.get("conversation_select")
    if sel and sel in st.session_state.get("conversations", {}):
        st.session_state["active_conversation"] = sel
        st.session_state["conversation_select"] = sel

# Helper para actualizar el modelo activo desde callbacks de Streamlit
def _set_active_model():
    sel = st.session_state.get("model_select")
    if sel:
        st.session_state["active_model"] = sel


def safe_rerun():
    """Recarga la app (compatible con varias versiones de Streamlit)."""
    try:
        if hasattr(st, "rerun"):
            st.rerun()
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        if hasattr(st, "experimental_request_rerun"):
            st.experimental_request_rerun()
    except Exception:
        pass


def _vision_models_available() -> List[str]:
    return [m for m in available_models() if model_supports_vision(m)]


def render_chat_message(message: dict) -> None:
    """Muestra un mensaje en el chat, con soporte para imágenes."""
    with st.chat_message(message["role"]):
        if message.get("image_b64"):
            import base64
            try:
                try:
                    st.image(
                        base64.b64decode(message["image_b64"]),
                        caption=message.get("content") or "Imagen",
                        width='stretch',
                    )
                except TypeError:
                    st.image(
                        base64.b64decode(message["image_b64"]),
                        caption=message.get("content") or "Imagen",
                        width='stretch',
                    )
            except Exception:
                st.markdown(message.get("content", "📷 Imagen"))
        elif "<img " in message.get("content", ""):
            st.markdown(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])


def render_chat_input_actions() -> None:
    """Coloca 🎤 y ➕ al costado del chat sin mover el widget de Streamlit."""
    st.html(
        """
        <script>
        (function () {
          function getDoc() {
            try {
              return window.parent && window.parent.document ? window.parent.document : document;
            } catch (e) {
              return document;
            }
          }

          function injectStyles(doc) {
            if (doc.getElementById("vora-chat-styles")) return;
            const style = doc.createElement("style");
            style.id = "vora-chat-styles";
            style.textContent = `
              .vora-chat-input-wrap {
                position: relative !important;
                display: flex !important;
                flex-direction: row !important;
                align-items: flex-end !important;
                gap: 0.4rem !important;
                width: 100% !important;
              }
              #vora-chat-bar {
                display: flex;
                flex-direction: row;
                gap: 0.35rem;
                flex-shrink: 0;
                padding-bottom: 0.35rem;
              }
              #vora-chat-bar button {
                font-size: 1.15rem;
                width: 2.5rem;
                height: 2.5rem;
                border-radius: 0.5rem;
                border: 1px solid rgba(128,128,128,0.35);
                background: rgba(128,128,128,0.06);
                cursor: pointer;
                line-height: 1;
                padding: 0;
              }
              #vora-chat-bar button:hover { background: rgba(128,128,128,0.14); }
              #vora-mic.listening {
                background: rgba(255,80,80,0.16);
                border-color: #e55;
              }
              .vora-chat-input-wrap [data-testid="stChatInput"] {
                flex: 1 1 auto !important;
                min-width: 0 !important;
              }
            `;
            doc.head.appendChild(style);
          }

          function getChatTextarea(doc) {
            return doc.querySelector('[data-testid="stChatInput"] textarea');
          }

          function setChatValue(doc, text) {
            const ta = getChatTextarea(doc);
            if (!ta) return false;
            const view = ta.ownerDocument.defaultView || window;
            const setter = Object.getOwnPropertyDescriptor(
              view.HTMLTextAreaElement.prototype,
              "value"
            ).set;
            setter.call(ta, text);
            ta.dispatchEvent(new InputEvent("input", {
              bubbles: true,
              inputType: "insertText",
              data: text
            }));
            ta.dispatchEvent(new Event("change", { bubbles: true }));
            ta.focus();
            return true;
          }

          function triggerFileUpload(doc) {
            const inputs = Array.from(doc.querySelectorAll('input[type="file"]'));
            const input = inputs.find(function (candidate) {
              return candidate.closest('[data-testid="stFileUploader"]');
            }) || inputs[0];

            if (input) {
              input.click();
              return true;
            }

            const uploader = doc.querySelector('[data-testid="stFileUploader"]');
            const clickable = uploader && uploader.querySelector("button, label");
            if (clickable) {
              clickable.click();
              return true;
            }

            return false;
          }

          function bindMic(btn, doc) {
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SR) {
              btn.disabled = true;
              btn.title = "Dictado: usa Chrome o Edge";
              return;
            }
            let recognition = null;
            let listening = false;
            let baseText = "";

            function stopListening() {
              listening = false;
              btn.classList.remove("listening");
              btn.textContent = "🎤";
              if (recognition) {
                try { recognition.stop(); } catch (e) {}
              }
            }

            btn.addEventListener("click", function () {
              if (listening) { stopListening(); return; }
              const ta = getChatTextarea(doc);
              baseText = ta && ta.value ? ta.value.trim() : "";
              recognition = new SR();
              recognition.lang = "es-ES";
              recognition.continuous = true;
              recognition.interimResults = true;
              recognition.onstart = function () {
                listening = true;
                btn.classList.add("listening");
                btn.textContent = "\u23F9\uFE0F";
              };
              recognition.onend = function () {
                listening = false;
                btn.classList.remove("listening");
                btn.textContent = "🎤";
              };
              recognition.onerror = function () { stopListening(); };
              recognition.onresult = function (event) {
                let sessionFinal = "";
                let interimChunk = "";
                for (let i = 0; i < event.results.length; i++) {
                  const part = event.results[i][0].transcript;
                  if (event.results[i].isFinal) sessionFinal += part;
                  else interimChunk += part;
                }
                const display = [baseText, sessionFinal, interimChunk]
                  .filter(function (p) { return p && p.trim(); })
                  .join(" ").trim();
                setChatValue(doc, display);
              };
              try { recognition.start(); } catch (e) {}
            });
          }

          function setup() {
            const doc = getDoc();
            if (doc.getElementById("vora-mic")) return;

            const chatRoot = doc.querySelector('[data-testid="stChatInput"]');
            if (!chatRoot || !chatRoot.parentElement) return;

            injectStyles(doc);

            const parent = chatRoot.parentElement;
            parent.classList.add("vora-chat-input-wrap");

            const bar = doc.createElement("div");
            bar.id = "vora-chat-bar";
            bar.innerHTML =
              '<button type="button" id="vora-mic" title="Dictar mensaje">🎤</button>' +
              '<button type="button" id="vora-attach" title="Adjuntar imagen o archivo">+</button>';

            parent.insertBefore(bar, chatRoot);

            bindMic(doc.getElementById("vora-mic"), doc);
            doc.getElementById("vora-attach").addEventListener("click", function () {
              triggerFileUpload(doc);
            });
          }

          let tries = 0;
          const timer = setInterval(function () {
            setup();
            tries += 1;
            const d = getDoc();
            if (d.getElementById("vora-mic") || tries > 30) clearInterval(timer);
          }, 200);
        })();
        </script>
        """,
    )

# ===============================================================
# FUNCIONALIDAD DE LA APLICACIÓN (HELPER FUNCTIONS)
# ===============================================================

def initialize_chat():
    """Inicializa o valida el estado del chat con estructura esperada (idéntico a tu versión)."""
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
                isinstance(msg, dict) and
                "role" in msg and msg["role"] in ["user", "assistant"] and
                "content" in msg and isinstance(msg["content"], str)
            ):
                valid_messages.append(msg)
        if len(valid_messages) != len(messages):
            st.info("ℹ️ Se corrigieron entradas de historial no válidas.")
            convs[active] = valid_messages


def call_ollama_api(user_input: str, images: Optional[List[str]] = None) -> Optional[str]:
    """
    Envía el mensaje a tu instancia local de Ollama con mecanismo de reintento exponencial.
    Usa /api/chat para modelos multimodales con imágenes, /api/generate para texto.
    """
    model_to_use = st.session_state.get("active_model", default_model())
    active = st.session_state.get("active_conversation", "Default")
    convo = st.session_state.get("conversations", {}).get(active, [])

    has_vision = model_supports_vision(model_to_use)

    # Si no se pasaron imágenes explícitas, buscar la última imagen del historial
    if not images and has_vision:
        for msg in reversed(convo):
            if msg.get("role") == "user" and msg.get("image_b64"):
                images = [msg["image_b64"]]
                break

    if images and has_vision:
        # /api/chat con formato de mensajes (soporta imágenes)
        messages = []
        for message in convo:
            content = message.get("content", "")
            if isinstance(content, str) and not content.startswith("[Archivo"):
                messages.append({
                    "role": message["role"],
                    "content": content,
                })

        messages.append({
            "role": "user",
            "content": user_input,
            "images": images,
        })

        payload = {
            "model": model_to_use,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": 4096},
        }
        endpoint = "http://localhost:11434/api/chat"
    else:
        # Texto puro: /api/generate con formato de chat
        history_messages = []
        for message in convo:
            role = message["role"]
            content = message["content"]
            if isinstance(content, str) and not content.startswith("[Archivo"):
                if role == "user":
                    history_messages.append(f"<|im_start|>user\n{content}<|im_end|>")
                else:
                    history_messages.append(f"<|im_start|>assistant\n{content}<|im_end|>")

        prompt = "".join(history_messages) + f"<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"

        payload = {
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
        }
        endpoint = "http://localhost:11434/api/generate"

    MAX_RETRIES = 4
    initial_delay = 2

    for attempt in range(MAX_RETRIES):
        try:
            spinner_text = f"🧠 Ollama está procesando... (Intento {attempt + 1}/{MAX_RETRIES})"
            try:
                spinner_cm = st.spinner(spinner_text, help="Indica que el modelo local está pensando en tu respuesta.")
            except TypeError:
                spinner_cm = st.spinner(spinner_text)
            
            with spinner_cm:
                response = requests.post(endpoint, json=payload, timeout=90)
                response.raise_for_status()
                result = response.json()

                # Manejo flexible de distintos formatos de respuesta
                text = ""
                if isinstance(result, dict):
                    if "message" in result and isinstance(result["message"], dict):
                        text = result["message"].get("content", "")
                    elif "response" in result and isinstance(result.get("response"), str):
                        text = result.get("response", "")
                    elif "results" in result and isinstance(result.get("results"), list) and result["results"]:
                        first = result["results"][0]
                        if isinstance(first, dict):
                            text = first.get("content") or first.get("text") or first.get("response") or ""
                        else:
                            text = str(first)
                    else:
                        text = result.get("content") or result.get("text") or ""
                elif isinstance(result, list) and result:
                    first = result[0]
                    if isinstance(first, dict):
                        text = first.get("content") or first.get("text") or ""
                    else:
                        text = str(first)
                else:
                    text = str(result)

                return text.strip()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt < MAX_RETRIES - 1:
                delay = initial_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                st.session_state["_last_api_error"] = f"FALLO DE CONEXIÓN: {type(e).__name__}. Verifica que Ollama esté ejecutándose."
                return None

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [429, 500, 502, 503, 504] and attempt < MAX_RETRIES - 1:
                delay = initial_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                body = e.response.text[:500] if e.response.text else ""
                import json as _json
                info = {"error_body": body, "model": payload.get("model"), "has_options": "options" in payload, "endpoint": endpoint}
                if "messages" in payload:
                    msgs = payload["messages"]
                    info["msg_count"] = len(msgs)
                    info["msg_roles"] = [m.get("role") for m in msgs]
                    info["msg_has_images"] = ["images" in m for m in msgs]
                    info["msg_content_lens"] = [len(m.get("content", "")) for m in msgs]
                else:
                    info["prompt_len"] = len(payload.get("prompt", ""))
                with open("vora_payload_dump.json", "w") as _f:
                    _json.dump(info, _f, indent=2)
                if status_code == 404:
                    current = st.session_state.get("active_model", default_model())
                    st.session_state["_last_api_error"] = f"Modelo no encontrado: '{current}'. Modelos disponibles: {', '.join(available_models())}"
                else:
                    st.session_state["_last_api_error"] = f"Error HTTP {status_code}: {e.response.reason}. Body: {body}"
                return None

        except Exception as e:
            st.session_state["_last_api_error"] = f"{type(e).__name__}: {e}"
            import traceback
            with open("vora_error.log", "a") as f:
                f.write(f"call_ollama_api error ({model_to_use}): {type(e).__name__}: {e}\n")
                traceback.print_exc(file=f)
            return None
    
    return None


def _process_file(f) -> bool:
    """Procesa un archivo subido. Devuelve True si se añadió algo al chat."""
    name = getattr(f, "name", "uploaded")
    content_type = getattr(f, "type", "") or ""
    data = f.read()
    text_extensions = (".txt", ".md", ".py", ".csv", ".json", ".log")
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
    lower = name.lower()
    is_text = any(lower.endswith(ext) for ext in text_extensions) or content_type.startswith("text")
    is_image = any(lower.endswith(ext) for ext in image_extensions) or content_type.startswith("image/")

    active = st.session_state.get("active_conversation", "Default")
    convs = st.session_state.setdefault("conversations", {})
    convs.setdefault(active, [])
    auto_interpret_enabled = st.session_state.get("auto_interpret", True)

    if is_text:
        try:
            text = data.decode("utf-8")
        except Exception:
            text = data.decode("latin-1", errors="replace")

        append_message(active, {"role": "user", "content": f"[Archivo: {name}]\n\n" + text})
        if auto_interpret_enabled:
            prompt = f"Por favor, interpreta y resume el siguiente archivo llamado '{name}':\n\n" + text
            resp = call_ollama_api(prompt)
            if resp:
                append_message(active, {"role": "assistant", "content": resp})
        return True

    if is_image:
        import base64
        b64 = base64.b64encode(data).decode("ascii")
        append_message(active, {
            "role": "user",
            "content": f"Imagen: {name}",
            "image_b64": b64,
        })
        if auto_interpret_enabled:
            current_model = st.session_state.get("active_model", default_model())
            prompt = (
                f"El usuario subió la imagen '{name}'. "
                "Descríbela en detalle en español: qué ves, colores, objetos, personas y texto visible."
            )
            if model_supports_vision(current_model):
                try:
                    resp = call_ollama_api(prompt, images=[b64])
                    if resp:
                        append_message(active, {"role": "assistant", "content": resp})
                    else:
                        err = st.session_state.pop("_last_api_error", "Error desconocido")
                        append_message(active, {
                            "role": "assistant",
                            "content": f"No pude analizar la imagen con '{current_model}'.\n\nDetalle: {err}",
                        })
                except Exception as e:
                    append_message(active, {
                        "role": "assistant",
                        "content": f"Error inesperado con '{current_model}': {type(e).__name__}: {e}",
                    })
            else:
                vision_models = _vision_models_available()
                if vision_models:
                    hint = f"**{vision_models[0]}**"
                    if len(vision_models) > 1:
                        hint += f" o **{vision_models[1]}**"
                    msg = (
                        f"⚠️ El modelo **{current_model}** no puede ver imágenes.\n\n"
                        f"Para obtener la descripción, cambia el modelo a {hint} "
                        "en la barra lateral y vuelve a subir la imagen."
                    )
                else:
                    msg = (
                        f"⚠️ El modelo **{current_model}** no soporta visión.\n\n"
                        "Instala un modelo multimodal: `ollama pull llava` o `ollama pull moondream`"
                    )
                append_message(active, {"role": "assistant", "content": msg})
        return True

    append_message(active, {
        "role": "user",
        "content": f"[Archivo subido: {name}] (tipo: {content_type or 'desconocido'})",
    })
    if auto_interpret_enabled:
        prompt = f"He subido un archivo llamado '{name}'. ¿Cómo puedo analizar su contenido?"
        resp = call_ollama_api(prompt)
        if resp:
            append_message(active, {"role": "assistant", "content": resp})
    return True


ensure_active_model_valid()
MODELS = available_models()

st.markdown(
    """
    <style>
    .main .block-container {
        padding-bottom: 1rem;
        max-width: 52rem;
    }
    [data-testid="stMain"] [data-testid="stFileUploader"] {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
        margin: 0;
        padding: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("model_select") != st.session_state.get("active_model"):
    if st.session_state.get("active_model") in MODELS:
        st.session_state["model_select"] = st.session_state["active_model"]

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.caption(f"Modelo: **{st.session_state.get('active_model')}**")

    if st.button("🔄 Recargar modelos", use_container_width=True):
        st.cache_data.clear()
        ensure_active_model_valid()
        if st.session_state.get("active_model") in MODELS:
            st.session_state["model_select"] = st.session_state["active_model"]
        safe_rerun()

    st.selectbox(
        "Modelo de IA",
        MODELS,
        key="model_select",
        on_change=_set_active_model,
        help="Para imágenes usa un modelo con visión: gemma4, gemma3:4b, llava, moondream...",
    )

    st.session_state["auto_interpret"] = st.checkbox(
        "Interpretar archivos automáticamente",
        value=st.session_state.get("auto_interpret", True),
        help="Al adjuntar un archivo, el modelo lo analiza y responde en el chat.",
    )
    st.caption("🎤 y ➕ están en la barra del mensaje (Chrome/Edge para voz).")

    st.markdown("---")
    st.subheader("💬 Conversaciones")

    convs = list(st.session_state.get("conversations", {}).keys()) or ["Default"]
    st.selectbox(
        "Conversación activa",
        convs,
        index=convs.index(st.session_state.get("active_conversation", "Default"))
        if st.session_state.get("active_conversation", "Default") in convs
        else 0,
        key="conversation_select",
        on_change=_set_active_conversation,
    )

    col_new, col_del = st.columns(2)
    with col_new:
        if st.button("➕ Nueva", use_container_width=True, key="new_chat_sidebar"):
            base = "Chat"
            existing = list(st.session_state.get("conversations", {}).keys())
            i = 1
            name = f"{base} {i}"
            while name in existing:
                i += 1
                name = f"{base} {i}"
            st.session_state.setdefault("conversations", {})[name] = []
            persist_conversation(name)
            st.session_state["active_conversation"] = name
            safe_rerun()
    with col_del:
        if st.button("🗑️ Eliminar", use_container_width=True, key="delete_chat_sidebar"):
            active = st.session_state.get("active_conversation", "Default")
            convs_dict = st.session_state.get("conversations", {})
            if active in convs_dict and len(convs_dict) > 1:
                del convs_dict[active]
                delete_conversation_from_db(active)
                st.session_state["active_conversation"] = list(convs_dict.keys())[0]
                safe_rerun()
            elif active in convs_dict:
                st.warning("No puedes eliminar la única conversación.")

    if st.button("🗑️ Limpiar archivos en cola", use_container_width=True):
        st.session_state["uploaded_files"] = []
        safe_rerun()

# --- ÁREA PRINCIPAL: chat ---
st.title("✨ Asistente Conversacional Local")
st.caption(
    f"**{st.session_state.get('active_conversation', 'Default')}** · "
    f"{st.session_state.get('active_model')}"
)

initialize_chat()

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
        _process_file(f)
        files_changed = True
        if fid:
            st.session_state["uploaded_files"].append(fid)

if files_changed:
    safe_rerun()

active = st.session_state.get("active_conversation", "Default")
messages = st.session_state.get("conversations", {}).get(active, [])

if not messages:
    st.info("👋 Escribe abajo. Usa **🎤** y **➕** en la barra del mensaje.")

for message in messages:
    render_chat_message(message)

user_prompt = st.chat_input("Escribe tu mensaje…")
render_chat_input_actions()

if user_prompt:
    convs = st.session_state.setdefault("conversations", {})
    active = st.session_state.get("active_conversation", "Default")
    convs.setdefault(active, [])

    full_response = call_ollama_api(user_prompt)
    append_message(active, {"role": "user", "content": user_prompt})
    if full_response:
        append_message(active, {"role": "assistant", "content": full_response})
    safe_rerun()


