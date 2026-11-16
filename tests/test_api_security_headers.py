"""Every API response carries the baseline security headers.

The API is deployed on a public host, so JSON responses as well as the
Swagger/ReDoc pages must not be sniffed, framed or leak referrer data.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import SECURITY_HEADERS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


@pytest.mark.parametrize("header,value", sorted(SECURITY_HEADERS.items()))
def test_health_response_has_security_header(header, value):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers[header] == value


def test_validation_errors_still_carry_security_headers():
    response = client.post("/generate", json={"prompt": ""})

    assert response.status_code == 422
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_not_found_responses_carry_security_headers():
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.headers["X-Frame-Options"] == "DENY"


def test_docs_page_is_framed_only_by_the_same_origin():
    response = client.get("/docs")

    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
