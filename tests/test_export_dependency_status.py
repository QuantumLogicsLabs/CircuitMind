"""Missing optional exporter dependencies are server errors, not bad requests.

`/export` used to map every module-level error to HTTP 422, so a server that
lacked ``schemdraw`` told the client its request was invalid. These tests pin
the distinction between a client error and a missing server dependency.
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app
from export.export_module import (
    ExportDependencyError,
    export_module,
    generate_svg,
)

client = TestClient(app)

LED_BODY = {
    "circuit_json": {
        "circuit_name": "LED",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"],
    }
}


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_generate_svg_reports_missing_schemdraw(monkeypatch):
    monkeypatch.setitem(sys.modules, "schemdraw", None)

    with pytest.raises(ExportDependencyError):
        generate_svg("LED", ["battery", "led"])


def test_export_module_tags_missing_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules, "schemdraw", None)

    payload = json.dumps(
        {
            "circuit_name": "LED",
            "components": ["battery", "led"],
            "connections": ["battery -> led"],
        }
    )
    result = export_module(payload, export_format="svg")

    assert result["status"] == "error"
    assert result["error_code"] == "DEPENDENCY_MISSING"
    assert "schemdraw" in result["message"]


def test_export_module_keeps_plain_runtime_errors_untagged():
    payload = json.dumps(
        {"circuit_name": "Empty", "components": [], "connections": []}
    )

    result = export_module(payload, export_format="svg")

    assert result["status"] == "error"
    assert "error_code" not in result
    assert "No drawable components" in result["message"]


def test_export_route_maps_missing_dependency_to_503(monkeypatch):
    monkeypatch.setattr(
        api_app,
        "export_module",
        lambda *args, **kwargs: {
            "status": "error",
            "error_code": "DEPENDENCY_MISSING",
            "message": "schemdraw is not installed. Run: pip install schemdraw",
        },
    )

    response = client.post("/export", json={**LED_BODY, "export_format": "svg"})

    assert response.status_code == 503
    assert "schemdraw" in response.json()["detail"]


def test_export_route_keeps_client_errors_at_422(monkeypatch):
    monkeypatch.setattr(
        api_app,
        "export_module",
        lambda *args, **kwargs: {
            "status": "error",
            "message": "Missing required fields: 'components' and 'connections'.",
        },
    )

    response = client.post("/export", json={**LED_BODY, "export_format": "spice"})

    assert response.status_code == 422
    assert "Missing required fields" in response.json()["detail"]
