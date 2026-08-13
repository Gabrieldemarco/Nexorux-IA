# Plan de Mejoras - Proyecto Nexorux IA

## 🐛 Bugfixes (sin riesgo de romper nada)

### 1. Importación al final del archivo en `media.py`
**Archivo**: `ui/media.py` (líneas 157-158)
**Problema**: Las importaciones están al final del archivo, después de las funciones que las usan. Esto es incorrecto y puede causar errores en algunos contextos de Python.
**Solución**: Mover las importaciones `from ui.chat_interface import initialize_chat_state` y `from ui.ollama_client import call_ollama_api, model_supports_vision, _vision_models_available` al inicio del archivo.

### 2. Duplicación de funciones entre `streamlit_app.py` y módulos
**Problema**: `streamlit_app.py` tiene copias idénticas de funciones ya definidas en los módulos:
- `call_ollama_api` (también en `ui/ollama_client.py`)
- `model_supports_vision` (también en `ui/ollama_client.py`)
- `_vision_models_available` (también en `ui/ollama_client.py`)
- `safe_rerun` (también en `ui/sidebar.py`)
- `load_conversations_from_db` (también en `core/__init__.py`)
- `append_message` (también en `core/__init__.py`)
- `persist_message`, `persist_conversation`, `delete_conversation_from_db` (también en `core/__init__.py`)
- `available_models`, `default_model`, `ensure_active_model_valid` (también en `ui/ollama_client.py`)
- `init_memory_db` (también en `core/__init__.py`)
- `get_available_ollama_models`, `bump_version` (también en `ui/ollama_client.py`)
- `render_chat_message`, `render_chat_input_actions`, `initialize_chat`, `_process_file` (solo en streamlit_app.py)

**Solución**: Refactorizar `streamlit_app.py` para importar desde los módulos en lugar de redefinir todo.

### 3. Prompt de texto inconsistente
**Archivos**: `streamlit_app.py` (línea 623) vs `ui/ollama_client.py` (línea 171)
**Problema**: 
- `streamlit_app.py` usa formato `<|im_start|>user\n...<|im_end|>` (formato llama3)
- `ui/ollama_client.py` usa formato `User: ...\nAssistant: ` (formato genérico)
Esto debe ser consistente para que funcione igual desde cualquier entrada.

### 4. `safe_rerun` con métodos obsoletos
**Problema**: `safe_rerun` intenta `experimental_rerun` y `experimental_request_rerun` que ya no existen en Streamlit moderno. Además está duplicado.
**Solución**: Simplificar a solo `st.rerun()`.

## ✨ Mejoras de calidad

### 5. DB_PATH y VERSION_PATH duplicados
**Problema**: Cada archivo define su propio `DB_PATH` y `VERSION_PATH`, lo que es propenso a errores si cambia la estructura.
**Solución**: Centralizar en `core/__init__.py` y `core/version_manager.py`.

### 6. Logging centralizado
**Problema**: Algunos errores van a `nexorux_error.log`, otros a `nexorux_payload_dump.json`, otros solo a `st.session_state`.
**Solución**: Unificar en un sistema de logging con timestamp y nivel.

## 📋 Orden sugerido de implementación

1. ✅ Mover imports en `media.py` al inicio
2. ✅ Centralizar DB_PATH y VERSION_PATH
3. ✅ Unificar `safe_rerun` (eliminar duplicado)
4. ✅ Alinear formato de prompts
5. ✅ Refactorizar `streamlit_app.py` para usar imports de módulos
6. ✅ Mejorar logging