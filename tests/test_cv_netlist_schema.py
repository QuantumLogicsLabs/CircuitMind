"""Tests for the pin-level netlist adapter used by the CV module."""

from cv_module.topology_extraction import adapt_netlist_to_schema


def _netlist():
    return {
        "metadata": {"total_components": 3, "total_connections": 3},
        "components": [
            {"id": "BATTERY_1", "type": "battery", "position": [10.0, 10.0]},
            {"id": "RESISTOR_2", "type": "resistor", "position": [20.0, 10.0]},
            {"id": "LED_3", "type": "led", "position": [30.0, 10.0]},
        ],
        "connections": [
            {"from": {"component": "BATTERY_1", "pin": "positive"},
             "to": {"component": "RESISTOR_2", "pin": "terminal_1"}},
            {"from": {"component": "RESISTOR_2", "pin": "terminal_2"},
             "to": {"component": "LED_3", "pin": "anode"}},
        ],
    }


def test_connections_use_component_names_not_pin_ids():
    adapted = adapt_netlist_to_schema(_netlist())
    assert adapted["connections"] == ["battery -> resistor", "resistor -> led"]


def test_components_stay_in_detection_order():
    adapted = adapt_netlist_to_schema(_netlist())
    assert adapted["components"] == ["battery", "resistor", "led"]


def test_parallel_connections_between_same_types_are_deduplicated():
    netlist = _netlist()
    netlist["connections"].append(
        {"from": {"component": "BATTERY_1", "pin": "negative"},
         "to": {"component": "RESISTOR_2", "pin": "terminal_2"}}
    )
    adapted = adapt_netlist_to_schema(netlist)
    assert adapted["connections"] == ["battery -> resistor", "resistor -> led"]


def test_pin_level_detail_is_preserved():
    adapted = adapt_netlist_to_schema(_netlist())
    assert adapted["netlist_detail"]["components"][0]["id"] == "BATTERY_1"


def test_empty_netlist_keeps_the_documented_fallback():
    adapted = adapt_netlist_to_schema({"components": [], "connections": []})
    assert adapted["components"] == ["battery", "resistor", "led"]
    assert adapted["connections"] == ["battery -> resistor", "resistor -> led"]


def test_unknown_component_ids_fall_back_to_the_id():
    adapted = adapt_netlist_to_schema({
        "components": [{"id": "RESISTOR_1", "type": "resistor"}],
        "connections": [
            {"from": {"component": "RESISTOR_1", "pin": "terminal_2"},
             "to": {"component": "GHOST_9", "pin": "terminal_1"}}
        ],
    })
    assert adapted["connections"] == ["resistor -> GHOST_9"]
