"""
CircuitMind - Dockerfile contract tests
tests/test_dockerfile.py

Guards the container settings that keep logs visible and avoid stale
bytecode inside the image. Parsed as text so the tests need no Docker.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
ENV_BLOCK = "".join(
    line for line in DOCKERFILE.splitlines(keepends=True)
    if line.startswith("ENV ") or line.startswith("    ")
)


def test_python_output_is_unbuffered():
    assert "PYTHONUNBUFFERED=1" in ENV_BLOCK


def test_bytecode_writing_is_disabled():
    assert "PYTHONDONTWRITEBYTECODE=1" in ENV_BLOCK


def test_container_runs_as_non_root():
    assert re.search(r"^USER appuser$", DOCKERFILE, re.MULTILINE)


def test_healthcheck_and_entrypoint_present():
    assert "HEALTHCHECK" in DOCKERFILE
    assert "api.app:app" in DOCKERFILE
