"""
CircuitMind - component knowledge base invariants
tests/test_component_db_consistency.py

Explain, Diagnose, Export and the rule-based generator each keep their own
view of component names. These tests pin the relationships that must hold
between those views so a one-sided edit is caught.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import component_resolver as resolver
from export import export_module


def test_every_entry_has_role_and_description():
    for name, entry in resolver.COMPONENT_DB.items():
        assert entry.get("role", "").strip(), name
        assert entry.get("description", "").strip(), name


def test_power_sources_have_power_role():
    for name in resolver.POWER_SOURCES:
        assert resolver.COMPONENT_DB[name]["role"] == "power source"


def test_component_groups_are_known_components():
    for group in (
        resolver.POWER_SOURCES,
        resolver.NEEDS_CURRENT_LIMIT,
        resolver.CURRENT_LIMITERS,
        resolver.LOAD_COMPONENTS,
    ):
        assert group <= resolver.KNOWN_COMPONENTS


def test_every_alias_points_at_a_known_component():
    missing = {alias: target for alias, target in resolver._ALIASES.items()
               if target not in resolver.COMPONENT_DB}
    assert missing == {}


def test_export_maps_cover_the_same_components():
    assert set(export_module.COMPONENT_MAP) == set(export_module.COMPONENT_VALUES)


def test_logic_gates_have_logic_role():
    gates = {"and", "or", "not", "nand", "nor", "xor", "xnor", "buffer"}
    assert gates <= resolver.KNOWN_COMPONENTS
    for gate in gates:
        assert resolver.COMPONENT_DB[gate]["role"] == "logic gate"
