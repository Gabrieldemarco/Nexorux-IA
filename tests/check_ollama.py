import requests

endpoints = [
    "http://localhost:11434/api/models",
    "http://localhost:11434/api/tags",
    "http://localhost:11434/api/list_models",
]

for url in endpoints:
    try:
        r = requests.get(url, timeout=3)
        print(f"URL: {url} -> status: {r.status_code}")
        text = r.text
        print(text[:1000])
        break
    except Exception as e:
        print(f"ERR {url}: {repr(e)}")
else:
    print("No endpoints reachable on localhost:11434")
