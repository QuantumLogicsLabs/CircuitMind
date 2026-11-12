"""
CircuitMind - API key authentication tests
tests/test_api_auth.py

verify_api_key() compared the header with "!=", which short-circuits on the
first differing byte. The comparison is now constant-time and rejects an
empty header without touching the key at all.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

import api.app as api_app  # noqa: E402

PROMPT = {"prompt": "make me an led circuit"}
SECRET = "test-secret-key"


@pytest.fixture(scope="module")
def client():
    return TestClient(api_app.app)


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", SECRET)


class TestApiKey:

    def test_correct_key_is_accepted(self, client, secured):
        response = client.post("/generate", json=PROMPT, headers={"x-api-key": SECRET})

        assert response.status_code == 200
        assert response.json()["circuit_name"] == "LED Circuit"

    def test_missing_key_is_rejected(self, client, secured):
        response = client.post("/generate", json=PROMPT)

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or missing API key"

    def test_wrong_key_is_rejected(self, client, secured):
        response = client.post("/generate", json=PROMPT, headers={"x-api-key": "wrong"})

        assert response.status_code == 401

    def test_empty_key_header_is_rejected(self, client, secured):
        response = client.post("/generate", json=PROMPT, headers={"x-api-key": ""})

        assert response.status_code == 401

    def test_open_access_when_no_key_is_configured(self, client, monkeypatch):
        monkeypatch.setattr(api_app, "API_KEY", None)

        response = client.post("/generate", json=PROMPT)

        assert response.status_code == 200
