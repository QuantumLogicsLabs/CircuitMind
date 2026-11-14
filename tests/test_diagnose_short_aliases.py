"""Regression tests: short-circuit detection through ground/load aliases.

check_short_circuit compared graph nodes (already normalized, so "v-"
became "v_") against the raw GROUND_KEYWORDS and required an exact match
for loads, so "battery -> v-" was not flagged while "battery -> light -> v-"
was falsely flagged.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import check_short_circuit, diagnose_circuit


def _has_short(connections):
    return any("Short circuit" in error for error in check_short_circuit(connections))


def test_v_minus_ground_is_recognised():
    assert _has_short(["battery -> v-"])


def test_ground_abbreviation_still_works():
    assert _has_short(["battery -> gnd"])


def test_load_alias_prevents_false_short():
    # "light" is an alias for LED, which is a load.
    assert not _has_short(["battery -> light -> v-"])


def test_canonical_load_prevents_false_short():
    assert not _has_short(["battery -> led -> v-"])


def test_diagnose_circuit_reports_short_through_v_minus():
    result = diagnose_circuit(
        {
            "circuit_name": "Short",
            "components": ["battery"],
            "connections": ["battery -> v-"],
        }
    )
    codes = {issue["code"] for issue in result["issues"]}
    assert "SHORT_CIRCUIT" in codes
    assert result["passed"] is False
