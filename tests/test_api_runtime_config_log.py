"""Startup configuration diagnostics tests."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import log_runtime_config


def _configure(monkeypatch, *, api_key=None, groq=None, redis=None):
    monkeypatch.setattr(api_app, "API_KEY", api_key)
    if groq is None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GROQ_API_KEY", groq)
    if redis is None:
        monkeypatch.delenv("RATE_LIMIT_REDIS_URL", raising=False)
    else:
        monkeypatch.setenv("RATE_LIMIT_REDIS_URL", redis)


def test_open_access_is_warned(monkeypatch, caplog):
    _configure(monkeypatch, api_key=None, groq="key", redis="redis://x")
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "CIRCUITMIND_API_KEY is not set" in caplog.text


def test_configured_key_does_not_warn(monkeypatch, caplog):
    _configure(monkeypatch, api_key="secret", groq="key", redis="redis://x")
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "CIRCUITMIND_API_KEY is not set" not in caplog.text


def test_missing_groq_key_is_warned(monkeypatch, caplog):
    _configure(monkeypatch, api_key="secret", groq=None, redis="redis://x")
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "GROQ_API_KEY is not set" in caplog.text


def test_blank_groq_key_counts_as_missing(monkeypatch, caplog):
    _configure(monkeypatch, api_key="secret", groq="   ", redis="redis://x")
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "GROQ_API_KEY is not set" in caplog.text


def test_in_memory_limiter_is_reported(monkeypatch, caplog):
    _configure(monkeypatch, api_key="secret", groq="key", redis=None)
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "rate limits are tracked per process" in caplog.text


def test_redis_backend_is_not_reported_as_missing(monkeypatch, caplog):
    _configure(monkeypatch, api_key="secret", groq="key", redis="redis://cache")
    with caplog.at_level(logging.INFO, logger="circuitmind"):
        log_runtime_config()
    assert "rate limits are tracked per process" not in caplog.text
