"""
CircuitMind - utils Module
utils/downloads.py

Builds the list of downloadable artifacts for a generated circuit so the
Streamlit UI (and any future client) shares one filename/mime convention.
"""

import json


def _slugify(name: str) -> str:
    slug = "".join(
        ch if ch.isalnum() else "_" for ch in str(name or "").lower()
    ).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "circuit"


def build_download_files(result: dict, svg_markup: str | None = None) -> list[dict]:
    """Return download descriptors for the circuit JSON and, if present, its SVG."""
    slug = _slugify(result.get("circuit_name"))
    files = [
        {
            "label": "⬇️ Circuit JSON",
            "filename": f"{slug}.json",
            "mime": "application/json",
            "data": json.dumps(result, indent=2),
        }
    ]
    if svg_markup:
        files.append({
            "label": "⬇️ Schematic SVG",
            "filename": f"{slug}.svg",
            "mime": "image/svg+xml",
            "data": svg_markup,
        })
    return files
