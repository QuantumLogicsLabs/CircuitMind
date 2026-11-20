"""
Tests for connection/component consistency warnings in the explain module.

A netlist whose connections mention a component that was never declared is
inconsistent; the explainer should surface that instead of silently rendering
an arrow chain that references a phantom part.
"""

from explain.explain_module import _check_connection_warnings, explain_circuit


def test_reference_to_undeclared_component_is_flagged():
    warnings = _check_connection_warnings(
        ["battery", "led"], ["battery -> resistor -> led"]
    )
    assert any("'resistor'" in w and "not listed in components" in w for w in warnings)


def test_fully_declared_connections_produce_no_warnings():
    warnings = _check_connection_warnings(
        ["battery", "resistor", "led"],
        ["battery -> resistor -> led"],
    )
    assert warnings == []


def test_ground_is_exempt_because_it_is_often_implicit():
    warnings = _check_connection_warnings(
        ["battery", "led"], ["battery -> led -> ground"]
    )
    assert warnings == []


def test_unknown_names_are_not_reported_here():
    warnings = _check_connection_warnings(
        ["battery", "gadget"], ["battery -> gadget"]
    )
    assert warnings == []


def test_aliases_resolve_before_comparison():
    warnings = _check_connection_warnings(
        ["battery", "led"], ["battery -> lamp"]
    )
    assert warnings == []


def test_each_missing_component_is_reported_once():
    warnings = _check_connection_warnings(
        ["battery"],
        ["battery -> resistor -> led", "battery -> resistor"],
    )
    assert len([w for w in warnings if "'resistor'" in w]) == 1
    assert len([w for w in warnings if "'led'" in w]) == 1


def test_dash_separator_is_supported():
    warnings = _check_connection_warnings(
        ["battery", "led"], ["battery -- resistor -- led"]
    )
    assert any("'resistor'" in w for w in warnings)


def test_explain_circuit_appends_connection_warnings():
    result = explain_circuit({
        "components": ["battery", "led"],
        "connections": ["battery -> resistor -> led"],
    })
    assert any("'resistor'" in w for w in result["warnings"])
