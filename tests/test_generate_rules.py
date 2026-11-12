"""
CircuitMind - Rule-based generation precedence tests
tests/test_generate_rules.py

generate_with_rules() returned the first rule with any keyword hit, so a
generic keyword listed early ("led") shadowed the specific request: "555 timer
with led" and "solar powered led" both produced an LED Circuit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules


class TestMostSpecificKeywordWins:

    def test_555_timer_beats_led(self):
        result = generate_with_rules("555 timer with led")

        assert result["circuit_name"] == "555 Timer Circuit"
        assert "555_timer" in result["components"]

    def test_solar_beats_led(self):
        result = generate_with_rules("solar powered led")

        assert result["circuit_name"] == "Solar Charging Circuit"

    def test_solar_beats_plural_leds(self):
        result = generate_with_rules("solar panel charging some leds")

        assert result["circuit_name"] == "Solar Charging Circuit"

    def test_timer_variant_beats_led(self):
        result = generate_with_rules("ne555 driven led")

        assert result["circuit_name"] == "555 Timer Circuit"


class TestSingleKeywordRulesStillMatch:

    def test_led_alone(self):
        assert generate_with_rules("make an led circuit")["circuit_name"] == "LED Circuit"

    def test_motor_alone(self):
        assert generate_with_rules("two motors")["circuit_name"] == "Motor Circuit"

    def test_generic_keywords_still_fall_back_to_unknown(self):
        assert generate_with_rules("mystery circuit")["circuit_name"] == "Unknown"

    def test_earlier_rule_wins_on_equal_length_keywords(self):
        # "led" and "fan" match the same number of characters; the LED rule is
        # declared first, so it keeps precedence.
        assert generate_with_rules("led and fan")["circuit_name"] == "LED Circuit"
