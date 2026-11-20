"""
UI test: the Generate tab offers the generated circuit as a download.

Runs the real Streamlit script through AppTest, clicks Generate with the
default prompt, and checks that the JSON download button renders.
"""

import os

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

_APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app_streamlit.py",
)


def test_generate_tab_renders_download_buttons():
    at = AppTest.from_file(_APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception

    at.button[0].click().run()

    assert not at.exception
    labels = [button.proto.label for button in at.get("download_button")]
    assert any("JSON" in label for label in labels)
    assert any("SVG" in label for label in labels)
