"""CORS configuration must be valid for browsers.

A wildcard origin list combined with ``allow_credentials`` is rejected by
browsers, so the settings helper has to disable credentials when ``*`` is
present. The default local-development origins keep credentials enabled.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import _cors_settings, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def _cors_middleware_options():
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware.kwargs
    raise AssertionError("CORSMiddleware is not registered")


def test_wildcard_origin_disables_credentials():
    origins, credentials = _cors_settings("*")

    assert origins == ["*"]
    assert credentials is False


def test_wildcard_among_explicit_origins_still_disables_credentials():
    origins, credentials = _cors_settings(
        "http://localhost:8501, *,http://example.com"
    )

    assert origins == ["http://localhost:8501", "*", "http://example.com"]
    assert credentials is False


def test_blank_entries_are_dropped_and_values_trimmed():
    origins, credentials = _cors_settings(
        " http://a.test ,, http://b.test ,  "
    )

    assert origins == ["http://a.test", "http://b.test"]
    assert credentials is True


def test_empty_origin_list_keeps_credentials_for_no_origins():
    origins, credentials = _cors_settings("   ")

    assert origins == []
    assert credentials is True


def test_default_app_allows_credentials_for_known_origins():
    options = _cors_middleware_options()

    assert options["allow_credentials"] is True
    assert "http://localhost:8501" in options["allow_origins"]


def test_preflight_response_echoes_origin_with_credentials():
    response = client.options(
        "/explain",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"
    assert response.headers["access-control-allow-credentials"] == "true"
