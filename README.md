"""
=== Nexorux IA Application ===

Version: v75
Architecture: Modular (Core/UI)
Status: Ready for Production

---

Features Implemented:
✅ Professional Streamlit UI
✅ Modular UI Components
✅ Database Management
✅ Multi-backend: Ollama + LM Studio
✅ Voice Input / TTS
✅ Image Vision Support
✅ Error Handling
✅ Testing Infrastructure

---

Main Components:
1. core/ - Core Business Logic
   ├── __init__.py - Database utilities
   └── ollama_client.py - Multi-backend LLM client

2. ui/ - Streamlit Frontend
   ├── streamlit_app.py - Main entry point (RECOMMENDED)
   ├── chat_interface.py - Chat state & config
   ├── ollama_client.py - AI integration
   ├── sidebar.py - UI controls
   ├── media.py - File processing
   └── voice_input.py - Voice controls

3. tests/ - Testing Suite

---

Quick Start:
1. Install dependencies: pip install -r requirements.txt
2. Run: streamlit run streamlit_app.py

---

Backends:
- Ollama: http://localhost:11434
- LM Studio: http://localhost:1234/v1

Select the backend from the sidebar panel.

---

Architecture Benefits:
- ✅ Maintainable (modular)
- ✅ Testable (structured tests)
- ✅ Secure (input validation)
- ✅ Scalable (separated concerns)
- ✅ Professional
"""
