import requests
import json

BASE = "http://localhost:11434"

def try_tags():
    url = BASE + "/api/tags"
    try:
        r = requests.get(url, timeout=5)
        print('GET', url, '->', r.status_code)
        print(json.dumps(r.json(), indent=2))
        return r.json()
    except Exception as e:
        print('ERR', url, repr(e))
        return None


def try_generate(model_name: str):
    url = BASE + "/api/generate"
    payload = {"model": model_name, "prompt": "Hola desde check_ollama_more.py", "stream": False}
    try:
        # Algunos modelos locales tardan en generar; usamos timeout mayor y un reintento
        r = requests.post(url, json=payload, timeout=60)
        print('POST', url, '->', r.status_code)
        try:
            print(json.dumps(r.json(), indent=2)[:2000])
        except Exception:
            print(r.text[:2000])
        return r
    except Exception as e:
        print('ERR', url, repr(e))
        # Intento adicional con streaming True (algunas versiones devuelven distinto comportamiento)
        try:
            payload2 = {"model": model_name, "prompt": "Hola desde check_ollama_more.py", "stream": True}
            r2 = requests.post(url, json=payload2, timeout=60)
            print('POST (stream) ->', r2.status_code)
            try:
                print(json.dumps(r2.json(), indent=2)[:2000])
            except Exception:
                print(r2.text[:2000])
            return r2
        except Exception as e2:
            print('ERR2', repr(e2))
        return None


if __name__ == '__main__':
    tags = try_tags()
    models = []
    if isinstance(tags, dict):
        models = [m.get('name') for m in tags.get('models', []) if isinstance(m, dict) and m.get('name')]
    elif isinstance(tags, list):
        models = tags

    print('Detected models:', models)
    if models:
        try_generate(models[0])
    else:
        print('No models found to test generation.')
