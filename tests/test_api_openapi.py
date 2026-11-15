"""
CircuitMind - OpenAPI contract tests
tests/test_api_openapi.py

Pins the published API surface: which routes exist, how they are tagged,
and that every mutating route advertises the X-API-Key header.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app

SPEC = api_app.app.openapi()

CORE_ROUTES = {
    "/generate",
    "/explain",
    "/diagnose",
    "/export",
    "/hint",
    "/generate-and-explain",
}


def test_health_routes_are_public_get():
    for path in ("/", "/health"):
        assert "get" in SPEC["paths"][path]
        assert "security" not in SPEC["paths"][path]["get"]


def test_core_routes_are_post_only():
    for path in CORE_ROUTES:
        ops = SPEC["paths"][path]
        assert set(ops) == {"post"}, path


def test_core_routes_are_tagged_core():
    for path in CORE_ROUTES:
        assert SPEC["paths"][path]["post"]["tags"] == ["core"]


def test_core_routes_document_the_api_key_header():
    for path in CORE_ROUTES:
        params = {
            p["name"] for p in SPEC["paths"][path]["post"].get("parameters", [])
            if p["in"] == "header"
        }
        assert "x-api-key" in params, path


def test_docs_endpoints_are_enabled():
    assert api_app.app.docs_url == "/docs"
    assert api_app.app.redoc_url == "/redoc"
