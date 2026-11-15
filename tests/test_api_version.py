"""
CircuitMind - API version consistency
tests/test_api_version.py

The root banner used to hardcode a version string that could drift from the
FastAPI app version shown in /docs and the OpenAPI schema.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import api.app as api_app

api_app.limiter.reset()
client = TestClient(api_app.app)


def test_root_reports_the_app_version():
    payload = client.get("/").json()
    assert payload["version"] == api_app.app.version


def test_openapi_reports_the_same_version():
    assert client.get("/openapi.json").json()["info"]["version"] == api_app.app.version
