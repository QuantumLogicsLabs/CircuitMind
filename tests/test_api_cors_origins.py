"""Regression tests for ALLOWED_ORIGINS parsing."""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("fastapi")
pytest.importorskip("slowapi")

from api.app import _parse_origins, allowed_origins


def test_origins_are_stripped_and_blanks_removed():
    raw = " http://a.example , http://b.example ,,"

    assert _parse_origins(raw) == [
        "http://a.example",
        "http://b.example",
    ]


def test_single_origin():
    assert _parse_origins("http://localhost:8501") == ["http://localhost:8501"]


def test_empty_setting_yields_no_origins():
    assert _parse_origins("   ,  ,") == []


def test_default_origins_are_clean():
    assert "http://localhost:8501" in allowed_origins
    assert all(o == o.strip() and o for o in allowed_origins)
