"""Access logging covers client address and crashing handlers.

The request middleware lives outside the exception middleware, so a handler
that raises would otherwise leave no access-log line. These tests pin that the
log still records method, path, client, status and duration.
"""

import logging
import sys
import os

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app


def _boom():
    raise RuntimeError("boom")


app.add_api_route("/__test_boom", _boom, methods=["GET"])


def test_success_log_includes_client_and_duration(caplog):
    caplog.set_level(logging.INFO, logger="circuitmind")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    line = next(m for m in caplog.messages if "/health" in m)
    assert "GET /health" in line
    assert "from testclient" in line
    assert "→ 200" in line
    assert "ms)" in line


def test_crashing_handler_is_logged(caplog):
    caplog.set_level(logging.INFO, logger="circuitmind")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/__test_boom")

    assert response.status_code == 500
    line = next(m for m in caplog.messages if "__test_boom" in m)
    assert "GET /__test_boom" in line
    assert "from testclient" in line
    assert "→ 500" in line
    assert "ms)" in line
