"""
Tests for requirements-dev.txt.

The test suite needs pytest itself and httpx (used by fastapi.testclient)
on top of the runtime dependencies. A dedicated dev requirements file
keeps `pip install -r requirements.txt` lean for production images.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DEV_REQS = _ROOT / "requirements-dev.txt"


def _entries() -> list[str]:
    return [
        line.strip()
        for line in _DEV_REQS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_dev_requirements_file_exists():
    assert _DEV_REQS.is_file()


def test_dev_requirements_include_runtime_dependencies():
    assert "-r requirements.txt" in _entries()


def test_dev_requirements_include_test_runner_and_client():
    entries = _entries()
    assert any(e.startswith("pytest") for e in entries)
    assert any(e.startswith("httpx") for e in entries)


def test_every_entry_is_an_option_or_a_requirement():
    for entry in _entries():
        assert entry.startswith("-r ") or not entry.startswith("-"), entry
