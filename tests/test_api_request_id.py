"""Request correlation IDs for the CircuitMind API.

Every response should carry an X-Request-ID header that matches the ID used in
the request log, and inbound IDs must be echoed only when they are safe.
"""

import logging
import re
import sys
import os

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def test_response_has_generated_request_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert _HEX32.match(response.headers["x-request-id"])


def test_valid_inbound_request_id_is_echoed():
    response = client.get("/health", headers={"X-Request-ID": "client.abc-123_X"})

    assert response.headers["x-request-id"] == "client.abc-123_X"


def test_request_ids_are_unique_per_request():
    first = client.get("/health").headers["x-request-id"]
    second = client.get("/health").headers["x-request-id"]

    assert first != second


def test_unsafe_inbound_request_id_is_replaced():
    for bad in ["has space", "line\nbreak", "x" * 65, "semi;colon"]:
        response = client.get("/health", headers={"X-Request-ID": bad})
        returned = response.headers["x-request-id"]

        assert returned != bad
        assert _HEX32.match(returned)


def test_request_id_appears_in_log(caplog):
    caplog.set_level(logging.INFO, logger="circuitmind")

    response = client.get("/health", headers={"X-Request-ID": "trace-42"})

    assert response.headers["x-request-id"] == "trace-42"
    assert any("[trace-42]" in message for message in caplog.messages)
