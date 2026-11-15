"""Deeper coverage for explain_circuit beyond the smoke tests."""

from explain.explain_module import explain_circuit, explain_circuits_batch

LED = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


def test_single_component_uses_singular_phrasing():
    result = explain_circuit({"components": ["resistor"], "connections": []})
    assert result["explanation"].startswith("This circuit uses a resistor")
    assert ", and " not in result["explanation"]


def test_two_components_are_joined_with_and():
    result = explain_circuit({"components": ["battery", "led"], "connections": []})
    assert "battery (power source)" in result["explanation"]
    assert ", and a led (light emitter)" in result["explanation"]


def test_many_components_are_comma_separated():
    result = explain_circuit(
        {"components": ["battery", "resistor", "led"], "connections": []}
    )
    assert result["explanation"].startswith("This circuit uses a battery (power source)")
    assert result["explanation"].rstrip(".").endswith(
        "a led (light emitter) that emits light when current flows through it"
    )


def test_led_without_resistor_is_warned_about():
    result = explain_circuit({"components": ["battery", "led"], "connections": []})
    assert any("current-limiting" in w for w in result["warnings"])


def test_unknown_component_is_listed_as_unknown():
    result = explain_circuit({"components": ["gizmo"], "connections": []})
    assert result["component_details"][0]["role"] == "unknown"
    assert any("Unknown component 'gizmo'" in w for w in result["warnings"])


def test_flow_description_is_included_in_the_explanation():
    result = explain_circuit(LED)
    assert "Current flows" in result["flow_description"]
    assert result["flow_description"] in result["explanation"]


def test_empty_circuit_has_no_flow_and_no_component_details():
    result = explain_circuit({"components": [], "connections": []})
    assert result["flow_description"] == ""
    assert result["component_details"] == []
    assert "No components provided" in result["explanation"]


def test_batch_explains_every_circuit():
    other = {"components": ["battery", "buzzer"], "connections": ["battery -> buzzer"]}
    results = explain_circuits_batch([LED, other])
    assert len(results) == 2
    assert all("explanation" in r for r in results)
    assert "buzzer" in results[1]["explanation"]
