"""Regression tests: .env.example must document every env var the API reads.

The example file claimed ALLOWED_ORIGINS defaulted to "*" (it does not) and
omitted CIRCUITMIND_API_KEY and RATE_LIMIT_REDIS_URL entirely.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (REPO_ROOT / "api" / "app.py").read_text(encoding="utf-8")
ENV_EXAMPLE = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

_ENV_PATTERN = re.compile(r"""os\.(?:environ\.get|getenv)\(\s*["']([A-Z0-9_]+)["']""")


def test_every_env_var_used_by_the_api_is_documented():
    used = set(_ENV_PATTERN.findall(APP_SOURCE))
    assert used, "expected api/app.py to read at least one env var"

    undocumented = sorted(name for name in used if name not in ENV_EXAMPLE)
    assert not undocumented, f"undocumented env vars: {undocumented}"


def test_allowed_origins_default_is_not_star():
    assert "default: *" not in ENV_EXAMPLE.lower()
    assert "http://localhost:8501" in ENV_EXAMPLE


def test_api_key_and_redis_url_are_mentioned():
    assert "CIRCUITMIND_API_KEY" in ENV_EXAMPLE
    assert "RATE_LIMIT_REDIS_URL" in ENV_EXAMPLE


def test_groq_key_still_documented():
    assert "GROQ_API_KEY" in ENV_EXAMPLE
