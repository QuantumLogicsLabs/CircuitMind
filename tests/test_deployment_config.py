"""Vercel must allow the API enough time for an LLM round trip.

The serverless default execution limit is shorter than the Groq request
timeout used by /generate, so a valid request could be killed mid-flight.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


def _api_build():
    for build in CONFIG["builds"]:
        if build["src"] == "api/app.py":
            return build
    raise AssertionError("api/app.py is not configured as a Vercel build")


def test_api_entrypoint_uses_the_python_runtime():
    assert _api_build()["use"] == "@vercel/python"


def test_execution_limit_covers_the_llm_timeout():
    max_duration = _api_build().get("config", {}).get("maxDuration")

    assert isinstance(max_duration, int)
    assert max_duration >= 30


def test_every_route_is_served_by_the_api():
    assert CONFIG["routes"] == [{"src": "/(.*)", "dest": "api/app.py"}]
