"""Regression tests for repo-level pytest configuration.

Root-level `pytest` used to abort with collection errors from the legacy
script-style suites (`generate/test_manual.py`, `diagnose/test_cases.py`).
Scope collection to the real test suite via testpaths.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pytest_ini_scopes_collection_to_tests():
    config = (REPO_ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "testpaths = tests" in config


def test_root_pytest_collects_without_errors():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "ERROR" not in output, output
    assert "tests/test_all_modules.py" in output
