"""
Tests for utils/downloads.py.

The Generate tab offers the circuit JSON (and the SVG preview, when the
export succeeded) as downloads. Filenames must be filesystem-safe and
derived from the circuit name.
"""

import json

from utils.downloads import build_download_files


def test_json_download_is_always_offered():
    files = build_download_files({"circuit_name": "LED Circuit"})
    assert len(files) == 1
    assert files[0]["filename"] == "led_circuit.json"
    assert files[0]["mime"] == "application/json"


def test_svg_download_is_added_when_markup_present():
    files = build_download_files({"circuit_name": "LED Circuit"}, "<svg/>")
    assert [f["mime"] for f in files] == ["application/json", "image/svg+xml"]
    assert files[1]["filename"] == "led_circuit.svg"
    assert files[1]["data"] == "<svg/>"


def test_json_payload_round_trips():
    circuit = {
        "circuit_name": "LED Circuit",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"],
    }
    decoded = json.loads(build_download_files(circuit)[0]["data"])
    assert decoded == circuit


def test_name_is_slugified():
    files = build_download_files({"circuit_name": "Half  Adder (2-bit)!"})
    assert files[0]["filename"] == "half_adder_2_bit.json"


def test_missing_name_falls_back_to_circuit():
    assert build_download_files({})[0]["filename"] == "circuit.json"
    assert build_download_files({"circuit_name": "   "})[0]["filename"] == "circuit.json"


def test_empty_svg_markup_is_ignored():
    files = build_download_files({"circuit_name": "Led"}, "")
    assert len(files) == 1
