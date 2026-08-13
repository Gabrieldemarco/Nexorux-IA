"""
Unit tests for core Ollama client.
"""
import json

import pytest

from core.ollama_client import (
    OLLAMA_BASE_URL,
    _build_payload,
    _extract_text,
    call_ollama,
    call_ollama_stream,
    check_connection,
    default_model,
    fetch_ollama_models,
    get_models,
    model_supports_vision,
    vision_models_available,
)


class TestHelpers:
    def test_model_supports_vision_known(self):
        assert model_supports_vision("llava") is True
        assert model_supports_vision("gemma4:latest") is True
        assert model_supports_vision("qwen2-vl") is True

    def test_model_supports_vision_negative(self):
        assert model_supports_vision("llama3:latest") is False
        assert model_supports_vision("mistral") is False

    def test_extract_text_from_dict_message(self):
        result = {"message": {"content": " hola "}}
        assert _extract_text(result) == "hola"

    def test_extract_text_from_dict_response(self):
        result = {"response": " mundo "}
        assert _extract_text(result) == "mundo"

    def test_extract_text_from_list(self):
        result = [{"content": "uno"}]
        assert _extract_text(result) == "uno"

    def test_extract_text_plain_string(self):
        assert _extract_text(" texto ") == "texto"


class TestPayload:
    def test_build_payload_text_mode(self):
        payload, endpoint = _build_payload("hi", "llama3:latest", [{"role": "user", "content": "prev"}])
        assert endpoint == f"{OLLAMA_BASE_URL}/api/generate"
        assert "prompt" in payload
        assert payload["model"] == "llama3:latest"

    def test_build_payload_vision_mode(self):
        payload, endpoint = _build_payload(
            "describe",
            "llava:latest",
            [{"role": "user", "content": "prev"}],
            images=["base64data"],
        )
        assert endpoint == f"{OLLAMA_BASE_URL}/api/chat"
        assert payload["messages"][-1]["images"] == ["base64data"]

    def test_build_payload_truncates_history(self):
        history = [{"role": "user", "content": f"m{i}"} for i in range(20)]
        payload, _ = _build_payload("hi", "llama3:latest", history)
        prompt = payload["prompt"]
        # should include only last 6 messages
        assert "m14" in prompt
        assert "m0" not in prompt


class TestFetchModels:
    def test_fetch_ollama_models_empty_on_failure(self, monkeypatch):
        class DummyResp:
            status_code = 500
            def raise_for_status(self):
                raise Exception("fail")
        monkeypatch.setattr("core.ollama_client.requests.get", lambda *a, **k: DummyResp())
        assert fetch_ollama_models() == []

    def test_get_models_alias(self, monkeypatch):
        monkeypatch.setattr("core.ollama_client.fetch_ollama_models", lambda: ["a"])
        assert get_models() == ["a"]

    def test_default_model_fallback(self, monkeypatch):
        monkeypatch.setattr("core.ollama_client.get_models", lambda: [])
        assert default_model() == "llama3:latest"

    def test_vision_models_available(self, monkeypatch):
        monkeypatch.setattr(
            "core.ollama_client.get_models",
            lambda: ["llava", "llama3:latest"],
        )
        assert vision_models_available() == ["llava"]

    def test_check_connection_true(self, monkeypatch):
        class DummyResp:
            status_code = 200
        monkeypatch.setattr("core.ollama_client.requests.get", lambda *a, **k: DummyResp())
        assert check_connection() is True

    def test_check_connection_false(self, monkeypatch):
        import requests
        monkeypatch.setattr(
            "core.ollama_client.requests.get",
            lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ConnectionError),
        )
        assert check_connection() is False
