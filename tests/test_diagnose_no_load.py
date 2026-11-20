"""
Tests for the NO_LOAD check in the diagnose module.

A battery wired only to switches, grounds, or other power sources cannot do
useful work; diagnosing that as a warning helps callers distinguish a
draft circuit from a complete one.
"""

from diagnose.diagnose_module import check_load_present, diagnose_circuit


def test_power_without_load_is_flagged():
    issue = check_load_present(["battery", "switch", "ground"])
    assert issue is not None
    assert issue["severity"] == "warning"
    assert issue["code"] == "NO_LOAD"


def test_power_with_led_is_fine():
    assert check_load_present(["battery", "resistor", "led"]) is None


def test_power_with_motor_is_fine():
    assert check_load_present(["power_supply", "dc_motor"]) is None


def test_each_load_kind_satisfies_the_check():
    for load in ("buzzer", "speaker", "capacitor", "relay", "display"):
        assert check_load_present(["battery", load]) is None, load


def test_no_power_means_no_load_warning():
    assert check_load_present(["resistor", "led"]) is None


def test_aliases_are_resolved_before_the_check():
    assert check_load_present(["9v_battery", "lamp"]) is None


def test_diagnose_circuit_emits_no_load_issue():
    result = diagnose_circuit({
        "components": ["battery", "switch", "ground"],
        "connections": ["battery -> switch -> ground"],
    })
    codes = [i["code"] for i in result["issues"]]
    assert "NO_LOAD" in codes
    assert result["summary"]["warnings"] >= 1
    assert any(i.startswith("Warning") and "No load" in i for i in result["legacy_issues"])


def test_diagnose_circuit_with_load_has_no_no_load_issue():
    result = diagnose_circuit({
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"],
    })
    assert "NO_LOAD" not in [i["code"] for i in result["issues"]]
