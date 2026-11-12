"""
CircuitMind - Ground reference detection tests
tests/test_diagnose_ground.py

check_ground_present() scanned the joined text for the bare keyword "common",
so a net such as "common_anode" counted as a ground reference and the missing
ground info was suppressed. It also compared raw component names against
POWER_SOURCES, missing aliases like "9v battery" or "vcc".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import check_ground_present, diagnose_circuit


class TestGroundKeywords:

    def test_ground_component_is_detected(self):
        assert check_ground_present(["battery", "ground"], ["battery -> ground"]) is None

    def test_common_net_is_detected(self):
        assert check_ground_present(["battery"], ["battery -> common"]) is None

    def test_gnd_and_ground_variants_are_detected(self):
        for node in ["gnd", "gnd_rail", "ground", "ground_plane", "0v", "v-", "negative"]:
            assert check_ground_present(["battery"], [f"battery -> {node}"]) is None

    def test_common_anode_is_not_a_ground_reference(self):
        message = check_ground_present(
            ["battery", "led"],
            ["battery -> led+", "battery -> common_anode"],
        )

        assert message is not None
        assert message.startswith("Info:")

    def test_keyword_inside_a_word_is_not_a_ground_reference(self):
        message = check_ground_present(["battery"], ["battery -> background_layer"])

        assert message is not None

    def test_no_power_source_means_no_info(self):
        assert check_ground_present(["led"], ["led -> resistor"]) is None


class TestPowerAliases:

    def test_power_alias_counts_as_power(self):
        for name in ["9v battery", "vcc", "solar panel"]:
            message = check_ground_present([name], [f"{name} -> led"])
            assert message is not None, name

    def test_power_alias_with_ground_is_satisfied(self):
        assert check_ground_present(["9v battery"], ["9v battery -> gnd"]) is None


class TestDiagnoseIntegration:

    def test_common_anode_raises_no_ground_info(self):
        result = diagnose_circuit({
            "circuit_name": "Anode net",
            "components":   ["battery", "led"],
            "connections":  ["battery -> led+", "battery -> common_anode"],
        })

        codes = [issue["code"] for issue in result["issues"]]
        assert "NO_GROUND" in codes

    def test_common_net_suppresses_no_ground_info(self):
        result = diagnose_circuit({
            "circuit_name": "Common net",
            "components":   ["battery", "led"],
            "connections":  ["battery -> led", "led -> common"],
        })

        codes = [issue["code"] for issue in result["issues"]]
        assert "NO_GROUND" not in codes
