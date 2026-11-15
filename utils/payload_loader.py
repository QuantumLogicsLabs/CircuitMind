"""
CircuitMind - UI Payload Loader
utils/payload_loader.py

Parses circuit JSON pasted into the Streamlit tabs. Shared by the Explain,
Diagnose and Export tabs so all three accept the same shapes and report the
same errors instead of raising on unexpected JSON.
"""

import json
from typing import Any


def load_circuit_payload(raw_text: str) -> tuple[dict | None, str | None]:
    """Return ``(payload, error)`` for a pasted circuit JSON document.

    Accepts either a bare circuit object or the ``{"circuit_json": {...}}``
    envelope the API uses. Parsing problems and non-object documents produce
    a message instead of an exception.
    """
    if not raw_text or not raw_text.strip():
        return None, "Paste a circuit JSON object first."

    try:
        data: Any = json.loads(raw_text)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

    if isinstance(data, dict) and "circuit_json" in data:
        data = data["circuit_json"]

    if not isinstance(data, dict):
        return None, (
            "Circuit JSON must be an object with 'components' and "
            "'connections'."
        )
    return data, None
