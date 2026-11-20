"""
Tests for additional component aliases in utils/component_resolver.py.

Netlists and prompts use common part names that are not themselves
canonical: "oscillator" / "timer_ic" for a 555, "seven segment" for a
display, "loudspeaker" for a speaker. Substring matching made
"oscillator" resolve to the OR gate, so these need explicit aliases.
"""

import pytest

from explain.explain_module import explain_circuit
from utils.component_resolver import COMPONENT_DB, _fuzzy_match, _normalize


def _resolve(name: str) -> str:
    return _fuzzy_match(_normalize(name))


@pytest.mark.parametrize("alias,canonical", [
    ("oscillator", "555_timer"),
    ("Oscillator", "555_timer"),
    ("timer_ic", "555_timer"),
    ("timer-ic", "555_timer"),
    ("Timer IC", "555_timer"),
    ("seven_segment", "display"),
    ("7_segment", "display"),
    ("Seven Segment", "display"),
    ("loudspeaker", "speaker"),
])
def test_alias_resolves_to_canonical(alias, canonical):
    assert _resolve(alias) == canonical
    assert canonical in COMPONENT_DB


def test_oscillator_no_longer_matches_the_or_gate():
    assert _resolve("oscillator") != "or"


def test_plain_gate_and_speaker_names_are_unchanged():
    assert _resolve("or") == "or"
    assert _resolve("or gate") == "or"
    assert _resolve("speaker") == "speaker"


def test_aliases_flow_through_explain():
    result = explain_circuit({
        "components": ["battery", "oscillator", "loudspeaker"],
        "connections": ["battery -> oscillator -> loudspeaker"],
    })
    names = [detail["name"] for detail in result["component_details"]]
    assert names == ["battery", "555_timer", "speaker"]
    assert not any("Unknown component" in w for w in result["warnings"])
