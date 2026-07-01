# test_gemini.py

import os
from dotenv import load_dotenv
try:
    import google.genai as genai
except ImportError:
    print("🚨 ERROR: Por favor, asegúrate de haber ejecutado 'pip install google-genai python-dotenv' en tu entorno.")
    exit()


def test_gemini_connection():
    """Intenta inicializar el cliente y realizar una llamada mínima a la API de Gemini."""

    print("="*60)
    print("🚀 INICIANDO PRUEBA DE CONEXIÓN GEMINI (Mínimo Código)")
    print("="*60)

    # 1. Cargar variables de entorno (Lee el archivo .env)
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("\n❌ FALLO CRÍTICO EN EL PASO DE CARGA:")
        print("Por favor, verifica que tu archivo '.env' exista en esta carpeta y contenga 'GEMINI_API_KEY=\"tu_clave\"'.")
        return

    try:
        # 2. Inicializar el cliente (El punto de fallo más común)
        client = genai.Client(api_key=api_key)
        print("✅ ÉXITO EN EL PASO DE CONEXIÓN: Cliente inicializado correctamente.")

        # 3. Realizar la llamada mínima (Prueba funcional real)
        prompt = "Escribe un haiku de tres líneas sobre el desarrollo web con Python."
        print(f"\n🤖 Enviando prompt de prueba: '{prompt}'")
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

        # 4. Imprimir resultado si es exitoso
        print("\n✨ RESULTADO DE LA LLAMADA API (¡ÉXITO!):")
        print("-------------------------------------------")
        print(response.text)
        print("-------------------------------------------")

    except Exception as e:
        # Captura cualquier error de conexión, autenticación o limitación de cuotas aquí
        print("\n🚨 ERROR FATAL DETECTADO:")
        print("-" * 30)
        print(f"Tipo de Error: {type(e).__name__}")
        print(f"Mensaje Detallado: {e}")
        print("-" * 30)


if __name__ == "__main__":
    test_gemini_connection()
