"""Rate limiting must key on the real client when running behind a proxy."""

import pytest
from starlette.requests import Request

from api.app import client_key


def make_request(forwarded_for=None, client=("203.0.113.7", 1234)):
    headers = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/generate",
        "headers": headers,
        "client": client,
        "scheme": "http",
        "server": ("testserver", 80),
        "query_string": b"",
    })


def test_uses_socket_address_by_default(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    assert client_key(make_request("198.51.100.9")) == "203.0.113.7"


@pytest.mark.parametrize("value", ["1", "true", "YES"])
def test_trusted_proxy_uses_first_hop(monkeypatch, value):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", value)
    assert client_key(make_request("198.51.100.9, 10.0.0.1")) == "198.51.100.9"


def test_trusted_proxy_without_header_falls_back(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert client_key(make_request()) == "203.0.113.7"


def test_blank_forwarded_header_falls_back(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert client_key(make_request("  , 10.0.0.1")) == "203.0.113.7"


def test_untrusted_value_ignores_header(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "0")
    assert client_key(make_request("198.51.100.9")) == "203.0.113.7"
