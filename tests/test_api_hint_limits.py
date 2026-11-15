"""Request-model limits for POST /hint.

The hint payload is client-supplied and forwarded into prompts/rule checks, so
its list fields must be bounded to avoid pathological payloads.
"""

import sys
import os

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import (
    app,
    HintRequest,
    HINT_MAX_IO,
    HINT_MAX_ITEMS,
    HINT_MAX_TITLE,
)

from fastapi.testclient import TestClient

client = TestClient(app)


def test_default_lists_are_not_shared_between_instances():
    first = HintRequest()
    second = HintRequest()

    first.inputs.append("x")

    assert second.inputs == []


@pytest.mark.parametrize("field", ["inputs", "outputs"])
def test_io_lists_accept_limit_and_reject_overflow(field):
    assert len(getattr(HintRequest(**{field: ["a"] * HINT_MAX_IO}), field)) == HINT_MAX_IO

    with pytest.raises(ValidationError):
        HintRequest(**{field: ["a"] * (HINT_MAX_IO + 1)})


@pytest.mark.parametrize("field", ["truth_table", "gates", "wires"])
def test_graph_lists_accept_limit_and_reject_overflow(field):
    rows = [{}] * HINT_MAX_ITEMS
    assert len(getattr(HintRequest(**{field: rows}), field)) == HINT_MAX_ITEMS

    with pytest.raises(ValidationError):
        HintRequest(**{field: rows + [{}]})


def test_problem_title_length_is_bounded():
    HintRequest(problem_title="t" * HINT_MAX_TITLE)

    with pytest.raises(ValidationError):
        HintRequest(problem_title="t" * (HINT_MAX_TITLE + 1))


def test_hint_endpoint_rejects_oversized_payload():
    response = client.post("/hint", json={"inputs": ["a"] * (HINT_MAX_IO + 1)})

    assert response.status_code == 422


def test_hint_endpoint_accepts_small_payload():
    response = client.post(
        "/hint",
        json={
            "problem_title": "Half adder",
            "inputs": ["A", "B"],
            "outputs": ["SUM"],
            "gates": [{"id": "A", "type": "INPUT"}],
            "wires": [],
        },
    )

    assert response.status_code == 200
