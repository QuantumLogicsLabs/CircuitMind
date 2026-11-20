"""
CircuitMind - utils Module
utils/circuit_state.py

Helpers for moving a generated circuit between the Streamlit tabs. The
Explain, Diagnose and Export tabs each own a JSON text area; reusing the
generated circuit means writing the same text into all three widget keys.
"""

import json


def circuit_text(result: dict) -> str:
    """Serialize a circuit for display in the JSON text areas."""
    return json.dumps(result, indent=2)


def reuse_values(result: dict) -> dict:
    """Map a generated circuit onto the widget keys of the other tabs."""
    text = circuit_text(result)
    return {"explain": text, "diag": text, "export_area": text}
