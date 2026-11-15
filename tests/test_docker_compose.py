"""Structural checks for docker-compose.yml.

Docker is not required: the file is parsed and the health-check wiring is
asserted so a broken healthcheck or an unguarded depends_on is caught in CI.
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

COMPOSE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _healthcheck_command(service):
    healthcheck = service["healthcheck"]
    test = healthcheck["test"]
    assert isinstance(test, list) and test[0] == "CMD"
    return " ".join(test)


def test_api_healthcheck_probes_the_uvicorn_port(compose):
    api = compose["services"]["api"]
    assert "7860/health" in _healthcheck_command(api)


def test_streamlit_healthcheck_does_not_probe_the_api_port(compose):
    streamlit = compose["services"]["streamlit"]
    command = _healthcheck_command(streamlit)
    assert "8501/_stcore/health" in command
    assert "7860" not in command


def test_streamlit_waits_for_a_healthy_api(compose):
    depends_on = compose["services"]["streamlit"]["depends_on"]
    assert depends_on == {"api": {"condition": "service_healthy"}}


def test_healthchecks_set_retries_and_start_period(compose):
    for name in ("api", "streamlit"):
        healthcheck = compose["services"][name]["healthcheck"]
        assert healthcheck["retries"] >= 3
        assert "start_period" in healthcheck
