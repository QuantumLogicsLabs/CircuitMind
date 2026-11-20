"""Tests for the /circuits/templates catalog endpoint."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app
from generate.generate import _RULES


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


@pytest.fixture()
def client():
    return TestClient(app)


def test_lists_every_rule_template(client):
    body = client.get("/circuits/templates").json()
    assert body["count"] == len(_RULES)
    assert len(body["templates"]) == len(_RULES)


def test_templates_preserve_rule_metadata(client):
    templates = client.get("/circuits/templates").json()["templates"]
    led = next(t for t in templates if t["name"] == "LED Circuit")
    source = next(r for r in _RULES if r[1] == "LED Circuit")
    assert led["keywords"] == list(source[0])
    assert led["components"] == list(source[2])
    assert led["connections"] == list(source[3])
    assert led["description"] == source[4]


def test_template_names_are_unique(client):
    templates = client.get("/circuits/templates").json()["templates"]
    names = [t["name"] for t in templates]
    assert len(names) == len(set(names))
    assert all(t["components"] for t in templates)


def test_route_is_documented(client):
    assert "get" in api_app.app.openapi()["paths"]["/circuits/templates"]
