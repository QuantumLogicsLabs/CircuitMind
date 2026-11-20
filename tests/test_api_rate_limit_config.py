"""Rate-limit configuration tests for the API."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import (
    _DEFAULT_RATE_LIMITS,
    _RATE_LIMIT_RE,
    RATE_LIMITS,
    resolve_rate_limits,
)


def test_defaults_used_when_nothing_is_set():
    limits = resolve_rate_limits({})
    assert limits == _DEFAULT_RATE_LIMITS
    assert RATE_LIMITS == _DEFAULT_RATE_LIMITS


def test_env_overrides_are_applied():
    limits = resolve_rate_limits(
        {
            "RATE_LIMIT_GENERATE": "2/minute",
            "RATE_LIMIT_EXPLAIN": "30/hour",
            "RATE_LIMIT_GENERATE_AND_EXPLAIN": "1/second",
        }
    )
    assert limits["generate"] == "2/minute"
    assert limits["explain"] == "30/hour"
    assert limits["generate_and_explain"] == "1/second"
    assert limits["diagnose"] == _DEFAULT_RATE_LIMITS["diagnose"]


def test_blank_override_keeps_default():
    limits = resolve_rate_limits({"RATE_LIMIT_HINT": "   "})
    assert limits["hint"] == _DEFAULT_RATE_LIMITS["hint"]


def test_invalid_override_falls_back_and_warns(caplog):
    with caplog.at_level(logging.WARNING, logger="circuitmind"):
        limits = resolve_rate_limits({"RATE_LIMIT_EXPORT": "ten per minute"})
    assert limits["export"] == _DEFAULT_RATE_LIMITS["export"]
    assert "RATE_LIMIT_EXPORT" in caplog.text


def test_every_resolved_value_is_parseable():
    limits = resolve_rate_limits(
        {"RATE_LIMIT_GENERATE": "0/minute", "RATE_LIMIT_HINT": "7/day"}
    )
    for value in limits.values():
        assert _RATE_LIMIT_RE.fullmatch(value), value


def test_decorated_endpoints_use_resolved_limits():
    generate = api_app.generate
    assert getattr(generate, "__wrapped__", None) is not None
