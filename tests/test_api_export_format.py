"""
CircuitMind - API export format tests
tests/test_api_export_format.py

ExportRequest validated export_format with a byte-for-byte set membership
check, so "SPICE", " gate_json " and an explicit null were rejected with 422
even though export_module() accepts all of them. The error also exposed a
Python set repr, whose order varies between runs.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

import api.app as api_app  # noqa: E402

CIRCUIT = {
    "circuit_name": "LED",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


@pytest.fixture(scope="module")
def client():
    return TestClient(api_app.app)


def _post(client, export_format):
    return client.post(
        "/export",
        json={"circuit_json": CIRCUIT, "export_format": export_format},
    )


class TestFormatIsNormalised:

    def test_uppercase_spice_is_accepted(self, client):
        response = _post(client, "SPICE")

        assert response.status_code == 200
        assert response.json()["format"] == "spice"

    def test_padded_gate_json_is_accepted(self, client):
        response = _post(client, " gate_json ")

        assert response.status_code == 200
        assert response.json()["format"] == "gate_json"

    def test_explicit_null_uses_the_default(self, client):
        response = _post(client, None)

        assert response.status_code == 200
        assert response.json()["format"] == "spice"


class TestInvalidFormat:

    def test_unknown_format_is_rejected_with_sorted_options(self, client):
        response = _post(client, "pdf")

        assert response.status_code == 422
        message = response.json()["detail"][0]["msg"]
        assert "gate_json, spice, svg" in message
