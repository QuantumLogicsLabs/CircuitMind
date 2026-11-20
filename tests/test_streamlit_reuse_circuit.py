"""
UI test: a generated circuit can be reused in the other tabs.

Clicks Generate, then the reuse button, and checks that the Explain,
Diagnose and Export text areas all receive the generated JSON.
"""

import json
import os

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

_APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app_streamlit.py",
)


def test_reuse_button_fills_other_tabs():
    at = AppTest.from_file(_APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception

    at.button[0].click().run()
    assert not at.exception

    at.button(key="reuse_generated_circuit").click().run()

    assert not at.exception
    for key in ("explain", "diag", "export_area"):
        payload = json.loads(at.text_area(key=key).value)
        assert payload["circuit_name"]
