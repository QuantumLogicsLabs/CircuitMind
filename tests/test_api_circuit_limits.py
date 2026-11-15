"""Request-model limits for circuit payloads.

/explain, /diagnose and /export accept an arbitrary circuit_json object. The
downstream modules scan every component and connection, so the lists must be
bounded at the API boundary.
"""

import sys
import os

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import (
    app,
    CircuitRequest,
    ExportRequest,
    CIRCUIT_MAX_COMPONENTS,
    CIRCUIT_MAX_CONNECTIONS,
)

client = TestClient(app)


def _circuit(components=None, connections=None) -> dict:
    return {
        "circuit_name": "Test",
        "components": components if components is not None else ["battery", "led"],
        "connections": connections if connections is not None else ["battery -> led"],
    }


@pytest.mark.parametrize("model", [CircuitRequest, ExportRequest])
def test_accepts_payload_at_limit(model):
    payload = _circuit(
        components=["resistor"] * CIRCUIT_MAX_COMPONENTS,
        connections=["a -> b"] * CIRCUIT_MAX_CONNECTIONS,
    )

    request = model(circuit_json=payload)

    assert len(request.circuit_json["components"]) == CIRCUIT_MAX_COMPONENTS


@pytest.mark.parametrize("model", [CircuitRequest, ExportRequest])
def test_rejects_too_many_components(model):
    payload = _circuit(components=["resistor"] * (CIRCUIT_MAX_COMPONENTS + 1))

    with pytest.raises(ValidationError):
        model(circuit_json=payload)


@pytest.mark.parametrize("model", [CircuitRequest, ExportRequest])
def test_rejects_too_many_connections(model):
    payload = _circuit(connections=["a -> b"] * (CIRCUIT_MAX_CONNECTIONS + 1))

    with pytest.raises(ValidationError):
        model(circuit_json=payload)


@pytest.mark.parametrize("model", [CircuitRequest, ExportRequest])
def test_rejects_non_list_fields(model):
    with pytest.raises(ValidationError):
        model(circuit_json={"components": "battery", "connections": []})
    with pytest.raises(ValidationError):
        model(circuit_json={"components": [], "connections": {"a": "b"}})


def test_empty_circuit_is_still_accepted():
    assert CircuitRequest(circuit_json={}).circuit_json == {}


@pytest.mark.parametrize("path", ["/explain", "/diagnose"])
def test_endpoints_reject_oversized_payload(path):
    payload = {"circuit_json": _circuit(components=["resistor"] * (CIRCUIT_MAX_COMPONENTS + 1))}

    response = client.post(path, json=payload)

    assert response.status_code == 422
