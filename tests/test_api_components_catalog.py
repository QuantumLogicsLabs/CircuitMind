"""Tests for the /components catalog endpoint."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app
from utils.component_resolver import COMPONENT_DB


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


@pytest.fixture()
def client():
    return TestClient(app)


def test_lists_every_known_component(client):
    response = client.get("/components")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(COMPONENT_DB)
    assert len(body["components"]) == len(COMPONENT_DB)


def test_entries_are_sorted_and_structured(client):
    body = client.get("/components").json()
    names = [c["name"] for c in body["components"]]
    assert names == sorted(names)
    battery = next(c for c in body["components"] if c["name"] == "battery")
    assert battery["role"] == "power source"
    assert battery["description"]
    assert set(battery) == {"name", "role", "description"}


def test_route_is_public_and_documented(client):
    assert "get" in api_app.app.openapi()["paths"]["/components"]
    response = client.get("/components")
    assert response.status_code == 200
