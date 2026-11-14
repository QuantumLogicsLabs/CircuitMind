"""Regression tests: malformed netlist connections must not crash the adapter.

adapt_netlist_to_schema indexed conn["from"]["component"] directly, so a
truncated pin-level record raised KeyError and aborted the whole CV pipeline.
"""

from cv_module.topology_extraction import adapt_netlist_to_schema

_COMPONENTS = [
    {"id": "BATTERY_1", "type": "battery"},
    {"id": "RESISTOR_1", "type": "resistor"},
    {"id": "LED_1", "type": "led"},
]


def test_missing_from_key_is_skipped():
    raw = {
        "components": _COMPONENTS,
        "connections": [
            {"to": {"component": "LED_1"}},
            {"from": {"component": "BATTERY_1"}, "to": {"component": "LED_1"}},
        ],
    }
    result = adapt_netlist_to_schema(raw)
    assert result["connections"] == ["BATTERY_1 -> LED_1"]
    assert result["skipped_connections"] == 1


def test_missing_component_key_is_skipped():
    raw = {
        "components": _COMPONENTS,
        "connections": [
            {"from": {"pin": "positive"}, "to": {"component": "LED_1"}},
            {"from": {"component": "BATTERY_1"}, "to": {"component": "RESISTOR_1"}},
        ],
    }
    result = adapt_netlist_to_schema(raw)
    assert result["connections"] == ["BATTERY_1 -> RESISTOR_1"]
    assert result["skipped_connections"] == 1


def test_non_dict_connection_is_skipped():
    raw = {
        "components": _COMPONENTS,
        "connections": ["BATTERY_1 -> LED_1", None, 42],
    }
    result = adapt_netlist_to_schema(raw)
    assert result["skipped_connections"] == 3


def test_non_string_endpoint_is_skipped():
    raw = {
        "components": _COMPONENTS,
        "connections": [
            {"from": {"component": 7}, "to": {"component": "LED_1"}},
        ],
    }
    result = adapt_netlist_to_schema(raw)
    assert result["skipped_connections"] == 1


def test_well_formed_netlist_skips_nothing():
    raw = {
        "components": _COMPONENTS,
        "connections": [
            {"from": {"component": "BATTERY_1"}, "to": {"component": "RESISTOR_1"}},
            {"from": {"component": "RESISTOR_1"}, "to": {"component": "LED_1"}},
        ],
    }
    result = adapt_netlist_to_schema(raw)
    assert result["connections"] == ["BATTERY_1 -> RESISTOR_1", "RESISTOR_1 -> LED_1"]
    assert result["skipped_connections"] == 0
