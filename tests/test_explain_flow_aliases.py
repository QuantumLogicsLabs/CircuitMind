"""
Tests for alias-aware effect notes in explain/explain_module.py.

The flow description appends an effect note based on the last node of a
connection chain. Netlists produced from images or written by hand often use
informal names ("lamp", "horn"), so the note must resolve aliases first.
"""

from explain.explain_module import _parse_flow, explain_circuit


def test_lamp_alias_gets_led_effect_note():
    flow = _parse_flow(["battery -> resistor -> lamp"])
    assert "LED to emit light" in flow


def test_light_alias_gets_led_effect_note():
    flow = _parse_flow(["battery -> light"])
    assert "LED to emit light" in flow


def test_horn_alias_gets_buzzer_effect_note():
    flow = _parse_flow(["battery -> horn"])
    assert "buzzer to produce sound" in flow


def test_beeper_alias_gets_buzzer_effect_note():
    flow = _parse_flow(["battery -> beeper"])
    assert "buzzer to produce sound" in flow


def test_motor_alias_with_separator_gets_motor_effect_note():
    flow = _parse_flow(["battery -- dc-motor"])
    assert "motor to spin" in flow


def test_canonical_last_node_still_gets_note():
    assert "LED to emit light" in _parse_flow(["battery -> led"])
    assert "buzzer to produce sound" in _parse_flow(["battery -> buzzer"])
    assert "motor to spin" in _parse_flow(["battery -> motor"])


def test_unknown_last_node_gets_no_effect_note():
    flow = _parse_flow(["battery -> gadget"])
    for note in ("emit light", "to spin", "produce sound"):
        assert note not in flow
    assert flow.rstrip().endswith("gadget.")


def test_explain_circuit_applies_alias_note():
    result = explain_circuit({
        "components": ["battery", "switch", "lamp"],
        "connections": ["battery -> switch -> lamp"],
    })
    assert "LED to emit light" in result["flow_description"]
    assert "LED to emit light" in result["explanation"]
