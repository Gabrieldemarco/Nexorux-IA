"""
Unified LLM client for Nexorux IA.
Supports both Ollama and LM Studio backends.
Single source of truth for communication with local LLM instances.
"""
import requests
import time
import json as _json
import traceback
from typing import Optional, List, Dict, Any, Generator, Literal

# ── Backend configuration ──────────────────────────────────────────

BackendType = Literal["ollama", "lmstudio"]

OLLAMA_BASE_URL = "http://localhost:11434"
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"

BACKENDS: Dict[BackendType, Dict[str, Any]] = {
    "ollama": {
        "label": "Ollama",
        "base_url": OLLAMA_BASE_URL,
        "chat_endpoint": f"{OLLAMA_BASE_URL}/api/chat",
        "generate_endpoint": f"{OLLAMA_BASE_URL}/api/generate",
        "models_endpoint": f"{OLLAMA_BASE_URL}/api/tags",
        "models_key": "models",
        "model_key": "name",
        "stream_chat_key": "message",
        "stream_generate_key": "response",
    },
    "lmstudio": {
        "label": "LM Studio",
        "base_url": LMSTUDIO_BASE_URL,
        "chat_endpoint": f"{LMSTUDIO_BASE_URL}/chat/completions",
        "generate_endpoint": f"{LMSTUDIO_BASE_URL}/chat/completions",
        "models_endpoint": f"{LMSTUDIO_BASE_URL}/models",
        "models_key": "data",
        "model_key": "id",
        "stream_chat_key": "choices",
        "stream_generate_key": "choices",
    },
}


def get_backend_config(backend: BackendType = "ollama") -> Dict[str, Any]:
    """Retorna la configuración del backend activo."""
    return BACKENDS.get(backend, BACKENDS["ollama"])


def set_active_backend(backend: BackendType) -> None:
    """Establece el backend activo globalmente."""
    import streamlit as st
    st.session_state["_nx_active_backend"] = backend


def get_active_backend() -> BackendType:
    """Obtiene el backend activo desde session_state."""
    import streamlit as st
    return st.session_state.get("_nx_active_backend", "ollama")


# ── MODELOS DISPONIBLES ──────────────────────────────────────────────

def fetch_models(backend: BackendType = "ollama") -> List[str]:
    """Consulta el backend y retorna la lista de modelos disponibles."""
    config = get_backend_config(backend)
    url = config["models_endpoint"]
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = []
        items = data.get(config["models_key"], [])
        if not isinstance(items, list):
            return []
        for m in items:
            if isinstance(m, dict):
                name = m.get(config["model_key"]) or m.get("name") or m.get("id") or m.get("model")
                if name:
                    models.append(str(name))
            else:
                models.append(str(m))
        return sorted(models)
    except Exception:
        return []


def check_connection(backend: BackendType = "ollama") -> bool:
    """Verifica si el servicio del backend está disponible."""
    config = get_backend_config(backend)
    url = config["models_endpoint"]
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def get_models(backend: BackendType = "ollama") -> List[str]:
    """Obtiene modelos disponibles para el backend dado."""
    return fetch_models(backend)


def default_model(backend: BackendType = "ollama") -> str:
    """Retorna el primer modelo disponible o fallback."""
    models = get_models(backend)
    return models[0] if models else "llama3:latest"


# ── MODELOS CON VISIÓN ───────────────────────────────────────────────

VISION_MODELS = [
    "llava", "bakllava", "moondream", "minicpm-v", "phi3-vision",
    "llama3.2-vision", "gemma3", "gemma3:4b", "gemma-3",
    "gemma4", "gemma4:latest", "qwen2-vl", "qwen-vl",
    "llava-llama3", "llava-13b", "llava-34b",
]


def model_supports_vision(model_name: str) -> bool:
    """Detecta si el modelo tiene soporte de visión."""
    model_lower = model_name.lower()
    return any(vision in model_lower for vision in VISION_MODELS)


def vision_models_available(models: Optional[List[str]] = None) -> List[str]:
    """Retorna modelos con soporte de visión."""
    if models is None:
        models = get_models()
    return [m for m in models if model_supports_vision(m)]


# ── PAYLOAD HELPERS ──────────────────────────────────────────────────

def _build_chat_payload(model: str, messages: List[Dict[str, Any]], stream: bool = True) -> Dict[str, Any]:
    """Payload en formato chat para LM Studio / Ollama."""
    return {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {"num_ctx": 4096},
    }


def _build_generate_payload(model: str, prompt: str, stream: bool = True) -> Dict[str, Any]:
    """Payload en formato generate para Ollama."""
    return {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {"num_ctx": 4096},
    }


def _build_payload(
    user_input: str,
    model: str,
    conversation_history: Optional[List[Dict]] = None,
    images: Optional[List[str]] = None,
    stream: bool = False,
    backend: BackendType = "ollama",
) -> tuple[Dict[str, Any], str]:
    """Construye el payload y endpoint según el backend."""
    config = get_backend_config(backend)
    history = conversation_history or []
    has_vision = model_supports_vision(model) and bool(images)

    if backend == "lmstudio":
        messages = []
        for msg in history:
            content = msg.get("content", "")
            if isinstance(content, str):
                messages.append({"role": msg["role"], "content": content})
        messages.append({"role": "user", "content": user_input, "images": images})
        payload = _build_chat_payload(model, messages, stream=stream)
        endpoint = config["chat_endpoint"]
    else:
        if has_vision:
            messages = []
            for msg in history:
                content = msg.get("content", "")
                if isinstance(content, str):
                    messages.append({"role": msg["role"], "content": content})
            messages.append({"role": "user", "content": user_input, "images": images})
            payload = _build_chat_payload(model, messages, stream=stream)
            endpoint = config["chat_endpoint"]
        else:
            if images:
                with open("nexorux_error.log", "a") as f:
                    import traceback
                    f.write(f"build_payload vision guard: backend={backend} model={model} dropped {len(images)} images\n")
                    traceback.print_stack(file=f)
            recent_history = history[-6:] if len(history) > 6 else history
            prompt_parts = []
            for msg in recent_history:
                role = msg["role"]
                content = msg["content"]
                if isinstance(content, str) and not content.startswith("[Archivo"):
                    prompt_parts.append(f"{'User' if role == 'user' else 'Assistant'}: {content}\n")
            prompt = "".join(prompt_parts) + f"User: {user_input}\nAssistant: "
            payload = _build_generate_payload(model, prompt, stream=stream)
            endpoint = config["generate_endpoint"]

    return payload, endpoint


def _extract_text(result: Any, backend: BackendType = "ollama") -> str:
    """Extrae texto de la respuesta según el formato del backend."""
    text = ""
    if backend == "lmstudio":
        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices and isinstance(choices[0], dict):
                msg = choices[0].get("message", {})
                text = msg.get("content", "") or choices[0].get("text", "")
        elif isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                text = first.get("content") or first.get("text") or ""
            else:
                text = str(first)
        else:
            text = str(result)
    else:
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


# ── LLAMADA NO-STREAM (BATCH) ────────────────────────────────────────

def call_ollama(
    user_input: str,
    model: str,
    conversation_history: Optional[List[Dict]] = None,
    images: Optional[List[str]] = None,
    max_retries: int = 4,
    timeout: int = 90,
    backend: BackendType = "ollama",
) -> Optional[str]:
    """Envía un mensaje al backend con reintento exponencial."""
    payload, endpoint = _build_payload(user_input, model, conversation_history, images, stream=False, backend=backend)
    initial_delay = 2
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            text = _extract_text(result, backend=backend)
            return text if text else None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt < max_retries - 1:
                time.sleep(initial_delay * (2 ** attempt))
            else:
                return None
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                time.sleep(initial_delay * (2 ** attempt))
            else:
                body = e.response.text[:500] if e.response.text else ""
                info = {"error": f"HTTP {status_code}", "body": body, "model": model, "endpoint": endpoint, "backend": backend}
                with open("nexorux_payload_dump.json", "w") as _f:
                    _json.dump(info, _f, indent=2)
                return None
        except Exception:
            with open("nexorux_error.log", "a") as f:
                f.write(f"call_ollama error backend={backend} model={model}: {type(e).__name__}: {e}\n")
                traceback.print_exc(file=f)
            return None
    return None


# ── LLAMADA STREAMING (TOKEN POR TOKEN) ──────────────────────────────

def call_ollama_stream(
    user_input: str,
    model: str,
    conversation_history: Optional[List[Dict]] = None,
    images: Optional[List[str]] = None,
    timeout: int = 90,
    backend: BackendType = "ollama",
) -> Generator[str, None, None]:
    """Envía un mensaje al backend y devuelve tokens en streaming."""
    payload, endpoint = _build_payload(user_input, model, conversation_history, images, stream=True, backend=backend)
    config = get_backend_config(backend)
    try:
        response = requests.post(endpoint, json=payload, timeout=timeout, stream=True)
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            text = ""
            if backend == "lmstudio":
                choices = data.get("choices", [])
                if choices and isinstance(choices[0], dict):
                    delta = choices[0].get("delta", {})
                    text = delta.get("content", "") or choices[0].get("text", "")
                if data.get("finish_reason") == "stop":
                    break
            else:
                if "response" in data:
                    text = data.get("response", "")
                elif "message" in data and isinstance(data["message"], dict):
                    text = data["message"].get("content", "")
                if data.get("done"):
                    break
            if text:
                yield text
    except Exception as e:
        with open("nexorux_error.log", "a") as f:
            f.write(f"call_ollama_stream error backend={backend} model={model}: {type(e).__name__}: {e}\n")
            traceback.print_exc(file=f)
        yield f"\n\n[Error: {type(e).__name__}]"