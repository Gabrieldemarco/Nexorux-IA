"""
Media and file upload handling for Streamlit frontend.
Manages file uploads, image processing, and interpretation.
"""
import streamlit as st
import base64
from typing import Dict, List, Optional
from pathlib import Path
from core import append_message
from core.ollama_client import call_ollama as _call_ollama, model_supports_vision, vision_models_available
from ui.chat_interface import initialize_chat_state



def _try_decode(data: bytes, name: str) -> str | None:
    """Intenta decodificar como texto. Devuelve None si es binario."""
    import re
    # Si tiene muchos bytes nulos o no-imprimibles, es binario
    if len(data) == 0:
        return ""
    sample = data[:4096]
    nulls = sample.count(b"\x00")
    printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    ratio = printable / max(len(sample), 1)
    if nulls > 10 or ratio < 0.6:
        return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("latin-1", errors="replace")


def _extract_pdf_text(data: bytes) -> str | None:
    """Extrae texto de un PDF usando PyMuPDF si está disponible."""
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip() or None
    except Exception:
        pass
    # Fallback: raw text extraction
    try:
        import re
        text = data.decode("latin-1", errors="replace")
        # Simple heuristic: find text between parentheses and after Tj operators
        parts = re.findall(r'\(([^)]*)\)\s*Tj', text)
        if parts:
            return "\n".join(parts).strip() or None
    except Exception:
        pass
    return None


def process_uploaded_file(f) -> bool:
    """Procesa un archivo subido. Devuelve True si se añadió algo al chat."""
    name = getattr(f, "name", "uploaded")
    content_type = getattr(f, "type", "") or ""
    data = f.read()
    file_size = len(data)
    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024*1024):.1f} MB"
    lower = name.lower()
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
    is_image = any(lower.endswith(ext) for ext in image_extensions) or content_type.startswith("image/")

    active = st.session_state.get("active_conversation", "Default")
    convs = st.session_state.setdefault("conversations", {})
    convs.setdefault(active, [])
    auto_interpret_enabled = st.session_state.get("auto_interpret", True)

    if is_image:
        b64 = base64.b64encode(data).decode("ascii")
        append_message(active, {
            "role": "user",
            "content": f"Imagen: {name}",
            "image_b64": b64,
        })
        if auto_interpret_enabled:
            current_model = st.session_state.get("active_model", "llama3:latest")
            prompt = (
                f"El usuario subió la imagen '{name}'. "
                "Descríbela en detalle en español: qué ves, colores, objetos, personas y texto visible."
            )
            if model_supports_vision(current_model):
                from ui.ollama_client import call_ollama_api as _call_ollama_api
                resp = _call_ollama_api(prompt, images=[b64])
                if resp:
                    append_message(active, {"role": "assistant", "content": resp})
                else:
                    err = st.session_state.pop("_last_api_error", "Error desconocido")
                    append_message(active, {
                        "role": "assistant",
                        "content": f"No pude analizar la imagen con '{current_model}'.\n\nDetalle: {err}",
                    })
            else:
                vision_models = vision_models_available()
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

    # Intentar extraer texto
    text = None
    source_info = ""
    if lower.endswith(".pdf"):
        text = _extract_pdf_text(data)
        source_info = " (texto extraído del PDF)"
    else:
        text = _try_decode(data, name)
        if text is not None:
            source_info = ""
        else:
            source_info = " (contenido binario)"

    MAX_TEXT_SIZE = 50000
    if text is not None and len(text) > MAX_TEXT_SIZE:
        text = text[:MAX_TEXT_SIZE] + f"\n\n[... archivo truncado de {size_str}]"

    if text is not None:
        content = f"[Archivo: {name} ({size_str})]{source_info}\n\n{text}"
        append_message(active, {"role": "user", "content": content})
        if auto_interpret_enabled:
            prompt = f"El usuario subió el archivo '{name}' ({size_str}). Resumí y analizá su contenido:\n\n" + text
            from ui.ollama_client import call_ollama_api as _call_ollama_api
            resp = _call_ollama_api(prompt)
            if resp:
                append_message(active, {"role": "assistant", "content": resp})
    else:
        append_message(active, {
            "role": "user",
            "content": f"[Archivo subido: {name} ({size_str})] (tipo: {content_type or 'desconocido'}, binario)",
        })
        if auto_interpret_enabled:
            prompt = f"El usuario subió un archivo binario llamado '{name}' de {size_str}. ¿Qué tipo de archivo es y cómo se analiza?"
            from ui.ollama_client import call_ollama_api as _call_ollama_api
            resp = _call_ollama_api(prompt)
            if resp:
                append_message(active, {"role": "assistant", "content": resp})
    return True


