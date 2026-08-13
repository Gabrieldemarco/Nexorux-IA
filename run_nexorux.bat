@echo off
echo Iniciando Nexorux IA...
echo.

:: Abrir terminal para Ollama
start "Ollama" cmd /k "ollama serve"

:: Esperar 3 segundos a que Ollama inicie
timeout /t 3 /nobreak >nul

:: Iniciar Streamlit
cd /d "%~dp0"
venv\Scripts\activate
streamlit run streamlit_app.py