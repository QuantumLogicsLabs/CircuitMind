"""
CircuitMind - API log privacy tests
tests/test_api_log_privacy.py

The API log lines for /generate, /hint and /generate-and-explain used to
echo the first 60 characters of user-supplied text. Prompts can contain
secrets or personal data, so the endpoints must log only a length.
"""

import sys
import os
import logging

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import api.app as api_app


SENTINEL = "sk-live-SECRET-do-not-log"


@pytest.fixture()
def client():
    api_app.limiter.reset()
    return TestClient(api_app.app)


@pytest.fixture()
def api_logs(caplog):
    caplog.set_level(logging.INFO, logger="circuitmind")
    return caplog


def test_generate_logs_prompt_length_not_prompt(client, api_logs, monkeypatch):
    monkeypatch.setattr(
        api_app, "generate_circuit", lambda prompt: {"components": [], "connections": []}
    )

    response = client.post("/generate", json={"prompt": f"{SENTINEL} led circuit"})

    assert response.status_code == 200
    assert SENTINEL not in api_logs.text
    assert "prompt_length=" in api_logs.text


def test_generate_and_explain_logs_prompt_length_not_prompt(client, api_logs, monkeypatch):
    monkeypatch.setattr(
        api_app, "generate_circuit", lambda prompt: {"components": [], "connections": []}
    )
    monkeypatch.setattr(api_app, "explain_circuit", lambda circuit: {"explanation": ""})
    monkeypatch.setattr(api_app, "diagnose_circuit", lambda circuit: {"passed": True, "issues": []})

    response = client.post(
        "/generate-and-explain", json={"prompt": f"{SENTINEL} led circuit"}
    )

    assert response.status_code == 200
    assert SENTINEL not in api_logs.text
    assert "prompt_length=" in api_logs.text


def test_hint_logs_title_length_not_title(client, api_logs, monkeypatch):
    monkeypatch.setattr(api_app, "generate_hint", lambda payload: {"hint": "ok", "source": "rule-based"})

    response = client.post("/hint", json={"problem_title": SENTINEL})

    assert response.status_code == 200
    assert SENTINEL not in api_logs.text
    assert "title_length=" in api_logs.text
