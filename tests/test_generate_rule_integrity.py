"""
CircuitMind - rule table integrity tests
tests/test_generate_rule_integrity.py

Every entry in the rule-based fallback table must stay internally
consistent: connections may only reference components the rule declares,
and every keyword must compile to a working pattern.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import _RULES, _build_rule_patterns, generate_with_rules


def test_rules_have_names_descriptions_and_components():
    for keywords, name, components, connections, description in _RULES:
        assert keywords and all(isinstance(k, str) and k for k in keywords)
        assert name and name != "Unknown"
        assert components and len(set(components)) == len(components)
        assert connections
        assert description


def test_connections_only_reference_declared_components():
    for _keywords, name, components, connections, _description in _RULES:
        declared = set(components)
        for connection in connections:
            parts = [p.strip() for p in connection.split("->")]
            assert len(parts) >= 2, (name, connection)
            assert all(parts), (name, connection)
            for part in parts:
                assert part in declared, (name, connection, part)


def test_every_keyword_matches_its_own_rule():
    compiled = _build_rule_patterns(_RULES)
    for (keywords, name, *_rest), (pattern, *_compiled) in zip(_RULES, compiled):
        for keyword in keywords:
            assert pattern.search(keyword), (name, keyword)


def test_first_keyword_selects_the_rule():
    for keywords, name, *_ in _RULES:
        assert generate_with_rules(keywords[0])["circuit_name"] == name


def test_plural_keyword_still_matches():
    assert generate_with_rules("two leds")["circuit_name"] == "LED Circuit"
    assert generate_with_rules("cooling fans")["circuit_name"] == "Fan Circuit"
    assert generate_with_rules("two buzzers")["circuit_name"] == "Buzzer Circuit"
    assert generate_with_rules("analog filters")["circuit_name"] == "RC Filter Circuit"


def test_unknown_rule_has_empty_components():
    result = generate_with_rules("warp core stabiliser")
    assert result["circuit_name"] == "Unknown"
    assert result["components"] == []
    assert result["connections"] == []
