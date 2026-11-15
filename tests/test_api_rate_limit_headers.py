"""Rate-limit response headers.

With headers_enabled, successful responses advertise the remaining quota so
clients can back off before they hit a 429, and the 429 response carries the
same headers.
"""

import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)

GENERATE_BODY = {"prompt": "make me a LED circuit"}


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_unlimited_route_has_no_quota_headers():
    response = client.get("/health")

    assert response.status_code == 200
    assert "x-ratelimit-limit" not in response.headers


def test_generate_response_advertises_quota():
    response = client.post("/generate", json=GENERATE_BODY)

    assert response.status_code == 200
    assert response.headers["x-ratelimit-limit"] == "5"
    assert int(response.headers["x-ratelimit-remaining"]) == 4
    assert float(response.headers["x-ratelimit-reset"]) >= 0


def test_explain_response_advertises_quota():
    body = {
        "circuit_json": {
            "circuit_name": "LED",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"],
        }
    }

    response = client.post("/explain", json=body)

    assert response.status_code == 200
    assert response.headers["x-ratelimit-limit"] == "10"
    assert int(response.headers["x-ratelimit-remaining"]) == 9


def test_exhausted_quota_returns_429_with_headers():
    for _ in range(5):
        assert client.post("/generate", json=GENERATE_BODY).status_code == 200

    response = client.post("/generate", json=GENERATE_BODY)

    assert response.status_code == 429
    assert response.headers["x-ratelimit-limit"] == "5"
    assert int(response.headers["x-ratelimit-remaining"]) == 0
