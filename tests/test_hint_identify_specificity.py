"""
CircuitMind - Identify keyword specificity tests
tests/test_hint_identify_specificity.py

_identify_circuit() returned the first known keyword found in the problem
text, so "demux" matched "mux" (substring) and a demultiplexer problem was
told it had built a Multiplexer. The longest matching keyword now wins.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _identify_circuit, generate_hint


class TestKeywordSpecificity:

    def test_demultiplexer_beats_multiplexer(self):
        payload = {"problem_title": "Demultiplexer Design"}
        assert _identify_circuit(payload) == "Demultiplexer"

    def test_demux_beats_mux(self):
        payload = {"problem_title": "Build a demux from logic gates"}
        assert _identify_circuit(payload) == "Demultiplexer"

    def test_multiplexer_still_identified(self):
        payload = {"problem_title": "Multiplexer"}
        assert _identify_circuit(payload) == "Multiplexer"

    def test_mux_still_identified(self):
        payload = {"problem_title": "2:1 mux"}
        assert _identify_circuit(payload) == "Multiplexer"

    def test_full_subtractor_is_preferred_over_shorter_keywords(self):
        payload = {"problem_title": "Full Subtractor", "problem_description": "using gates"}
        assert _identify_circuit(payload) == "Full Subtractor"


class TestIdentifyResponse:

    def test_demux_identify_reply_names_demultiplexer(self):
        result = generate_hint({
            "request_type": "identify",
            "problem_title": "Demultiplexer with enable",
        })

        assert result["circuit_name"] == "Demultiplexer"
        assert "Demultiplexer" in result["hint"]
