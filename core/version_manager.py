"""
Version management module for Nexorux IA.
Handles version tracking and server startup for version checks.
"""
import threading
from pathlib import Path

VERSION_PATH = Path(__file__).parent.with_name("version.json")


def bump_version() -> None:
    """Incrementa la versión para notificar a otros clientes."""
    import json as _json
    try:
        with open(VERSION_PATH) as _f:
            v = _json.load(_f)
    except Exception:
        v = {"version": 0}
    v["version"] = v.get("version", 0) + 1
    with open(VERSION_PATH, "w") as _f:
        _json.dump(v, _f)



