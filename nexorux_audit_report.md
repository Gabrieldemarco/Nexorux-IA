# AuditorÃ­a Completa de Nexorux IA â€” Asistente Conversacional Local

**Fecha:** 12/07/2026  
**VersiÃ³n analizada:** v75  
**Arquitectura:** Modular (Core/API/UI)  
**Frontend:** Streamlit  
**Backend:** FastAPI  
**Base de datos:** SQLite  
**Motor de IA:** Ollama (local)

---

## 1. ESTRUCTURA DEL PROYECTO

```
Nexorux IA/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ __main__.py
â”œâ”€â”€ streamlit_app.py          â† Entry point principal (Streamlit)
â”œâ”€â”€ run_Nexorux IA.py               â† Script de lanzamiento alternativo
â”œâ”€â”€ run.bat / run.sh          â† Scripts de inicio
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ version.json
â”œâ”€â”€ .env / .gitignore
â”‚
â”œâ”€â”€ api/                      â† Backend FastAPI
â”‚   â”œâ”€â”€ __init__.py           â† Factory de la app FastAPI
â”‚   â”œâ”€â”€ __main__.py
â”‚   â”œâ”€â”€ routes.py             â† Endpoints REST
â”‚   â””â”€â”€ ollama_client.py      â† Cliente Ollama para API
â”‚
â”œâ”€â”€ core/                     â† LÃ³gica central
â”‚   â”œâ”€â”€ __init__.py           â† DB, conversaciones, mensajes
â”‚   â””â”€â”€ version_manager.py    â† Servidor de versiones HTTP
â”‚
â”œâ”€â”€ ui/                       â† Componentes Streamlit
â”‚   â”œâ”€â”€ chat_interface.py     â† Estado del chat, page config
â”‚   â”œâ”€â”€ media.py              â† Procesamiento de archivos/imÃ¡genes
â”‚   â”œâ”€â”€ ollama_client.py      â† Cliente Ollama para UI (DUPLICADO)
â”‚   â”œâ”€â”€ sidebar.py            â† Barra lateral completa
â”‚   â”œâ”€â”€ voice_input.py        â† Componente de voz (HTML/JS)
â”‚   â””â”€â”€ voice_premium.py      â† Voz premium (no analizado)
â”‚
â”œâ”€â”€ tests/                    â† Tests
â”‚   â”œâ”€â”€ check_db.py / 2 / 3
â”‚   â”œâ”€â”€ check_ollama.py / more
â”‚   â”œâ”€â”€ test_12msgs.py
â”‚   â”œâ”€â”€ test_gemini.py
â”‚   â”œâ”€â”€ test_gemma4_history.py
â”‚   â””â”€â”€ test_vision.py
â”‚
â””â”€â”€ backup/                   â† Backup
```

---

## 2. DUPLICACIÃ“N DE CÃ“DIGO â€” PROBLEMA CRÃTICO

### 2.1 `call_ollama_api()` duplicado en 3 lugares

| Archivo | LÃ­neas | Diferencias |
|---------|--------|-------------|
| `streamlit_app.py` | 564-713 | Spinner con emoji ðŸ§ , texto "Ollama estÃ¡ procesando..." |
| `ui/ollama_client.py` | 112-268 | Spinner con â³, texto mÃ¡s corto |
| `api/ollama_client.py` | 1-61 | VersiÃ³n simplificada, sin reintentos ni spinners |

**Impacto:** Cualquier bugfix o mejora en la lÃ³gica de llamada a Ollama debe aplicarse en 3 archivos distintos. Ya hay divergencias (diferentes mensajes de spinner, diferente manejo de errores).

### 2.2 `model_supports_vision()` duplicado

- `streamlit_app.py` lÃ­neas 278-285
- `ui/ollama_client.py` lÃ­neas 84-91

**Impacto:** Si se agrega un nuevo modelo con visiÃ³n, hay que actualizar ambos archivos.

### 2.3 `_vision_models_available()` duplicado

- `streamlit_app.py` lÃ­neas 308-309
- `ui/ollama_client.py` lÃ­neas 94-96

### 2.4 Funciones de base de datos duplicadas

Las siguientes funciones existen tanto en `streamlit_app.py` como en `core/__init__.py`:

| FunciÃ³n | streamlit_app.py | core/__init__.py |
|---------|-----------------|-------------------|
| `init_memory_db()` | 58-85 | 13-49 |
| `load_conversations_from_db()` | 88-113 | 52-82 |
| `persist_conversation()` | 116-127 | 118-129 |
| `delete_conversation_from_db()` | 129-135 | 132-137 |
| `persist_message()` | 137-160 | 140-182 |
| `append_message()` | 163-167 | 210-217 |

**Impacto:** `streamlit_app.py` tiene su propia copia de TODAS las funciones de base de datos, con ligeras diferencias (ej: `core/__init__.py` tiene `model` column support, `rename_conversation_in_db()`, `load_messages_for_conversation()`, `get_last_message_id()` que NO estÃ¡n en `streamlit_app.py`).

### 2.5 `bump_version()` duplicado

- `streamlit_app.py` lÃ­neas 45-55
- `core/version_manager.py` lÃ­neas 11-21
- `ui/ollama_client.py` lÃ­neas 99-109

### 2.6 `_start_version_server()` duplicado

- `streamlit_app.py` lÃ­neas 19-39
- `core/version_manager.py` lÃ­neas 24-43

### 2.7 `available_models()` / `default_model()` / `ensure_active_model_valid()` duplicado

- `streamlit_app.py` lÃ­neas 228-249
- `ui/ollama_client.py` lÃ­neas 62-81

### 2.8 `_process_file()` vs `process_uploaded_file()`

- `streamlit_app.py` lÃ­neas 716-804 (`_process_file`)
- `ui/media.py` lÃ­neas 59-152 (`process_uploaded_file`)

Son casi idÃ©nticas pero con diferencias: `ui/media.py` tiene soporte para PDF con PyMuPDF, detecciÃ³n binaria mÃ¡s robusta, y truncado de texto.

---

## 3. SEGURIDAD

### 3.1 Problemas detectados

| # | Problema | Archivo | LÃ­nea | Severidad |
|---|----------|---------|-------|-----------|
| 1 | CORS con `allow_origins=["*"]` | `api/__init__.py` | 31 | Media |
| 2 | CORS con `allow_origins=["*"]` | `api/routes.py` | 24 | Media |
| 3 | `unsafe_allow_html=True` en `st.markdown` | `streamlit_app.py` | 333, 829 | Baja |
| 4 | No hay rate limiting en API | `api/routes.py` | - | Media |
| 5 | No hay autenticaciÃ³n ni API keys | General | - | Baja (es local) |
| 6 | No hay sanitizaciÃ³n de input de usuario antes de enviar a Ollama | `ui/ollama_client.py` | 112-268 | Baja |
| 7 | Puerto 8765 expuesto en localhost sin auth | `core/version_manager.py` | 39 | Baja |

### 3.2 Buenas prÃ¡cticas

- âœ… Uso de `PRAGMA foreign_keys = ON`
- âœ… Uso de parÃ¡metros parametrizados en SQL (no concatenaciÃ³n)
- âœ… Timeouts en requests a Ollama (5s y 90s)
- âœ… Manejo de excepciones en operaciones de archivos

---

## 4. PERFORMANCE

### 4.1 Problemas

| # | Problema | Archivo | Impacto |
|---|----------|---------|---------|
| 1 | `st.cache_data(ttl=30)` en `_fetch_ollama_models()` | `ui/ollama_client.py` | Bajo (correcto) |
| 2 | `st.cache_data(ttl=60)` en `get_available_ollama_models()` | `streamlit_app.py` | Bajo (correcto) |
| 3 | Carga completa de DB en cada render | `streamlit_app.py` lÃ­nea 972 | Medio |
| 4 | `safe_rerun()` con try/except pasivo | MÃºltiples archivos | Bajo |
| 5 | LÃ­mite de historial a 6 mensajes | `ui/ollama_client.py` lÃ­nea 135 | Medio (pierde contexto) |
| 6 | Sin paginaciÃ³n en endpoints de conversaciones | `api/routes.py` | Bajo |

### 4.2 Buenas prÃ¡cticas

- âœ… WAL mode en SQLite (`PRAGMA journal_mode=WAL`)
- âœ… CachÃ© de modelos con TTL
- âœ… Reintento exponencial en llamadas a Ollama
- âœ… Timeout de 90s en requests largos

---

## 5. ERROR HANDLING

### 5.1 Problemas

| # | Problema | Archivo | LÃ­nea |
|---|----------|---------|-------|
| 1 | `safe_rerun()` traga excepciones silenciosamente | MÃºltiples | - |
| 2 | Errores de API guardados en `_last_api_error` pero no siempre mostrados | `streamlit_app.py` | 676 |
| 3 | `st.stop()` en error de conexiÃ³n sin graceful degradation | `streamlit_app.py` | 225 |
| 4 | No hay logging estructurado (solo print y archivo plano) | General | - |
| 5 | `except Exception: pass` en varios lugares | MÃºltiples | - |

### 5.2 Buenas prÃ¡cticas

- âœ… Reintento con backoff exponencial (2^attempt)
- âœ… Dump de payload a archivo para debugging
- âœ… Traceback guardado en `Nexorux IA_error.log`
- âœ… ValidaciÃ³n de estructura de mensajes en `initialize_chat()`

---

## 6. DEPENDENCIAS

### 6.1 `requirements.txt`

```
streamlit
requests
python-dotenv
pillow
PyAudio
speechrecognition
pyttsx3
playsound
pydub
fastapi
uvicorn
google-genai
```

### 6.2 Problemas

| # | Problema | Detalle |
|---|----------|---------|
| 1 | Sin versiones fijas | Riesgo de breaking changes |
| 2 | `google-genai` solo usado en tests | No deberÃ­a estar en requirements principal |
| 3 | `PyAudio` difÃ­cil de instalar en Windows | Requiere rueda precompilada |
| 4 | `playsound` obsoleto | Usar `playsound2` o alternativa |
| 5 | Falta `fitz` (PyMuPDF) | Se importa en `ui/media.py` pero no estÃ¡ en requirements |
| 6 | Sin archivo `pyproject.toml` o `setup.py` | No es instalable como paquete |

---

## 7. ARQUITECTURA â€” PROBLEMAS ESTRUCTURALES

### 7.1 Monolito disfrazado de modular

Aunque hay carpetas `api/`, `core/`, `ui/`, en la prÃ¡ctica:

- `streamlit_app.py` es un monolito de 984 lÃ­neas que contiene TODO duplicado
- Los mÃ³dulos en `ui/` y `core/` estÃ¡n infrautilizados
- `streamlit_app.py` no importa `ui/sidebar.py` ni `ui/chat_interface.py` â€” los ignora completamente

### 7.2 Dos entry points compitiendo

- `streamlit_app.py` (el que realmente se ejecuta)
- `run_Nexorux IA.py` (solo imprime mensajes, no arranca nada)

### 7.3 API FastAPI no conectada al frontend

- `api/routes.py` define endpoints REST completos
- Pero `streamlit_app.py` NO usa la API â€” se conecta directamente a Ollama
- La API y la UI son dos aplicaciones independientes que no se comunican

### 7.4 Servidor de versiones HTTP duplicado

- Se inicia en `streamlit_app.py` lÃ­nea 42
- Y tambiÃ©n en `core/version_manager.py` lÃ­nea 46
- El segundo lanzamiento falla silenciosamente (puerto ocupado)

---

## 8. CALIDAD DE CÃ“DIGO

### 8.1 Problemas

| # | Problema | Ejemplo |
|---|----------|---------|
| 1 | CÃ³digo muerto | `ui/sidebar.py`, `ui/chat_interface.py`, `ui/media.py` no son importados por `streamlit_app.py` |
| 2 | Strings mÃ¡gicos | URLs de Ollama hardcodeadas en mÃºltiples archivos |
| 3 | Falta de type hints consistentes | Algunas funciones usan `Optional`, otras no |
| 4 | Nombres inconsistentes | `_process_file()` vs `process_uploaded_file()` |
| 5 | CÃ³digo comentado | Varias lÃ­neas comentadas sin explicaciÃ³n |
| 6 | Sin tests unitarios | Los tests existentes son scripts de verificaciÃ³n manual |
| 7 | `import json as _json` repetido | En casi todos los archivos |

### 8.2 Buenas prÃ¡cticas

- âœ… Uso de `pathlib.Path` en lugar de strings
- âœ… Docstrings en la mayorÃ­a de funciones
- âœ… Manejo de mÃºltiples formatos de respuesta de Ollama
- âœ… DetecciÃ³n de cambios de otros clientes vÃ­a version.json

---

## 9. RECOMENDACIONES PRIORIZADAS

### ðŸ”´ CrÃ­ticas (hacer ya)

1. **Eliminar duplicaciÃ³n de `streamlit_app.py`**: Refactorizar para que `streamlit_app.py` importe desde `core/` y `ui/` en lugar de tener sus propias copias. Esto eliminarÃ­a ~600 lÃ­neas de cÃ³digo duplicado.

2. **Unificar `call_ollama_api()`**: Mover a `core/` y que tanto UI como API lo importen.

3. **Eliminar `streamlit_app.py` como monolito**: Convertirlo en un archivo delgado que solo importe componentes.

### ðŸŸ¡ Altas (siguiente sprint)

4. **Conectar API FastAPI con el frontend**: Que `streamlit_app.py` use la API REST en lugar de llamar a Ollama directamente.

5. **Agregar versiones fijas en `requirements.txt`**.

6. **Agregar `fitz` (PyMuPDF) a requirements**.

7. **Unificar `_process_file()` y `process_uploaded_file()`**.

### ðŸŸ¢ Medias (prÃ³ximos sprints)

8. **Agregar logging estructurado** (ej: `loguru` o `structlog`).

9. **Agregar tests unitarios con pytest**.

10. **Crear `pyproject.toml`** para hacer el proyecto instalable.

11. **Reemplazar `playsound` por `playsound2`**.

12. **Agregar rate limiting a la API**.

### ðŸ”µ Bajas (mejora continua)

13. **Centralizar constantes** (URLs de Ollama, timeouts, etc.) en un archivo de configuraciÃ³n.

14. **Mejorar manejo de errores**: Reemplazar `except Exception: pass` con logging adecuado.

15. **Agregar paginaciÃ³n a endpoints de conversaciones**.

16. **Documentar la arquitectura** en README.md.

---

## 10. MÃ‰TRICAS

| MÃ©trica | Valor |
|---------|-------|
| LÃ­neas totales de cÃ³digo | ~2,500+ |
| Archivos Python | 18 |
| Funciones duplicadas | 10+ |
| Entry points | 2 (streamlit_app.py, run_Nexorux IA.py) |
| Cobertura de tests | ~0% (tests manuales) |
| Dependencias | 12 |
| Archivos no utilizados | 3 (ui/sidebar.py, ui/chat_interface.py, ui/media.py no son importados) |

---

## 11. CONCLUSIÃ“N

Nexorux IA es un proyecto funcional con buena base arquitectÃ³nica (modular, separaciÃ³n de capas), pero sufre de **duplicaciÃ³n masiva de cÃ³digo** porque `streamlit_app.py` fue escrito como monolito antes de que existieran los mÃ³dulos `core/` y `ui/`. 

**El problema principal** es que `streamlit_app.py` (984 lÃ­neas) contiene copias de casi todas las funciones que ya existen en `core/__init__.py` y `ui/ollama_client.py`, y ademÃ¡s **no importa** los componentes de `ui/sidebar.py`, `ui/chat_interface.py` ni `ui/media.py`, dejÃ¡ndolos como cÃ³digo muerto.

**La prioridad #1** deberÃ­a ser refactorizar `streamlit_app.py` para que sea un archivo delgado que importe desde los mÃ³dulos existentes, eliminando la duplicaciÃ³n y reactivando el cÃ³digo muerto.
