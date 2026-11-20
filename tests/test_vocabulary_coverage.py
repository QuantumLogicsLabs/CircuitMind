"""
Cross-module vocabulary coverage.

The generate templates, the explain/diagnose component database and the
export symbol/value maps are maintained separately. These tests keep them
in sync: every analog component a template can produce must be explainable
and exportable.
"""

from explain.explain_module import explain_circuit
from export.export_module import COMPONENT_MAP, COMPONENT_VALUES
from generate.generate import _RULES, generate_circuit
from utils.component_resolver import COMPONENT_DB, _fuzzy_match, _normalize

# Logic gates, logic I/O ports and the ground rail are described structurally
# (gate JSON / netlist connections) rather than as discrete SPICE parts.
_LOGIC_ONLY = {
    "and", "or", "not", "nand", "nor", "xor", "xnor", "buffer",
    "ground", "input_a", "input_b", "input_c", "sum_output", "carry_output",
}

_ANALOG_CIRCUITS = {
    "LED Circuit",
    "Motor Circuit",
    "Buzzer Circuit",
    "Fan Circuit",
    "Temperature Sensor",
    "Solar Charging Circuit",
    "555 Timer Circuit",
    "RC Filter Circuit",
}


def _resolve(name: str) -> str:
    return _fuzzy_match(_normalize(name))


def test_export_maps_cover_every_analog_component():
    expected = set(COMPONENT_DB) - _LOGIC_ONLY
    assert expected - set(COMPONENT_MAP) == set()
    assert expected - set(COMPONENT_VALUES) == set()


def test_export_maps_have_identical_keys():
    assert set(COMPONENT_MAP) == set(COMPONENT_VALUES)


def test_analog_rule_templates_only_use_known_components():
    analog_rules = [rule for rule in _RULES if rule[1] in _ANALOG_CIRCUITS]
    assert len(analog_rules) == len(_ANALOG_CIRCUITS)
    for _keywords, name, components, _connections, _desc in analog_rules:
        unknown = [c for c in components if _resolve(c) not in COMPONENT_DB]
        assert unknown == [], f"{name} uses unknown components: {unknown}"


def test_resolvable_rule_components_are_exportable():
    for _keywords, name, components, _connections, _desc in _RULES:
        for component in components:
            resolved = _resolve(component)
            if resolved in COMPONENT_DB and resolved not in _LOGIC_ONLY:
                assert resolved in COMPONENT_MAP, f"{name}: {resolved} missing from COMPONENT_MAP"


def test_analog_templates_explain_without_unknown_component_warnings():
    for prompt in (
        "make me a LED circuit",
        "build a motor circuit",
        "make a buzzer",
        "make a fan",
        "temperature sensor",
        "solar charging circuit",
        "555 timer",
        "rc filter",
    ):
        result = generate_circuit(prompt)
        explanation = explain_circuit(result)
        unknown = [w for w in explanation["warnings"] if "Unknown component" in w]
        assert unknown == [], f"{prompt}: {unknown}"
