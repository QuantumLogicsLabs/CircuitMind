"""Alias coverage for common classroom and hobbyist component names.

The knowledge base already mapped a handful of synonym names; these tests pin
the expanded set so explain/diagnose stop reporting everyday names as unknown.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.component_resolver import COMPONENT_DB, KNOWN_COMPONENTS, _fuzzy_match, _normalize

NEW_ALIASES = {
    "battery_pack": "battery",
    "battery_bank": "battery",
    "aa_battery": "battery",
    "button_cell": "battery",
    "psu": "power_supply",
    "usb": "power_supply",
    "usb_power": "power_supply",
    "dc_supply": "power_supply",
    "adapter": "power_supply",
    "electric_motor": "dc_motor",
    "photo_resistor": "ldr",
    "temperature_sensor": "thermistor",
}


@pytest.mark.parametrize("alias,canonical", sorted(NEW_ALIASES.items()))
def test_alias_resolves_to_canonical_component(alias, canonical):
    assert _fuzzy_match(_normalize(alias)) == canonical
    assert canonical in COMPONENT_DB


@pytest.mark.parametrize("alias", sorted(NEW_ALIASES))
def test_alias_never_shadows_a_canonical_key(alias):
    assert alias not in KNOWN_COMPONENTS


def test_case_and_separator_variants_resolve():
    assert _fuzzy_match(_normalize("USB Power")) == "power_supply"
    assert _fuzzy_match(_normalize("Battery-Pack")) == "battery"
    assert _fuzzy_match(_normalize("TEMP SENSOR")) == "thermistor"


def test_unknown_names_stay_unresolved():
    assert _fuzzy_match(_normalize("gizmo")) == "gizmo"
