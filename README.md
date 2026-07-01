# Vora — Asistente Conversacional Local

App en Streamlit que se conecta a **Ollama** para correr LLMs localmente con soporte de múltiples conversaciones, imágenes, subida de archivos y dictado por voz.

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com) instalado y corriendo (`ollama serve`)
- Al menos un modelo descargado (`ollama pull llama3`, `ollama pull gemma3`, etc.)

## Instalación

```bash
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Uso

```bash
streamlit run streamlit_app.py
```

## Modelos con visión

Para usar imágenes necesitás un modelo multimodal:
```
ollama pull gemma3
ollama pull llava
ollama pull moondream
```

## Estructura

```
vora/
├── streamlit_app.py    # App principal
├── app.py              # API FastAPI secundaria
├── tests/              # Scripts de diagnóstico
├── vora_memory.sqlite3 # Base de datos local (autogenerada)
└── requirements.txt    # Dependencias
```
