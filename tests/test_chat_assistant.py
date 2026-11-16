"""Unit tests for the Streamlit assistant helper.

The chat helper is responsible for the request timeout and for never showing
provider errors to the user. Groq is stubbed, so these run offline.
"""

import logging
from types import SimpleNamespace

import pytest

from utils import chat_assistant as chat


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)


class _Completion:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class FakeGroq:
    calls: list = []
    content = "A resistor limits current."
    error = None

    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        FakeGroq.calls.append({"api_key": self.api_key, **kwargs})
        if FakeGroq.error is not None:
            raise FakeGroq.error
        return _Completion(FakeGroq.content)


@pytest.fixture(autouse=True)
def reset_fake(monkeypatch):
    FakeGroq.calls = []
    FakeGroq.content = "A resistor limits current."
    FakeGroq.error = None
    monkeypatch.delenv("CHAT_TIMEOUT", raising=False)
    yield


MESSAGES = [
    {"role": "assistant", "content": "Hello!", "timestamp": 1},
    {"role": "user", "content": "What is a resistor?", "timestamp": 2},
]


def test_missing_api_key_returns_helpful_message_without_a_request():
    response, error = chat.chat_reply(MESSAGES, api_key="", client_factory=FakeGroq)

    assert response is None
    assert error == chat.MISSING_KEY_MESSAGE
    assert FakeGroq.calls == []


def test_api_key_falls_back_to_the_environment(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "env-key")

    response, error = chat.chat_reply(MESSAGES, client_factory=FakeGroq)

    assert error is None
    assert response == "A resistor limits current."
    assert FakeGroq.calls[0]["api_key"] == "env-key"


def test_request_shape_and_system_prompt():
    response, error = chat.chat_reply(
        MESSAGES, api_key="key", client_factory=FakeGroq
    )

    assert error is None
    assert response == "A resistor limits current."

    call = FakeGroq.calls[0]
    assert call["model"] == chat.DEFAULT_CHAT_MODEL
    assert call["max_tokens"] == chat.CHAT_MAX_TOKENS
    assert call["timeout"] == chat.DEFAULT_CHAT_TIMEOUT
    assert call["messages"][0] == {
        "role": "system",
        "content": chat.SYSTEM_PROMPT,
    }
    assert call["messages"][1:] == [
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "What is a resistor?"},
    ]


def test_history_is_limited_to_the_most_recent_turns():
    messages = [
        {"role": "user", "content": f"message {index}"} for index in range(10)
    ]

    chat.chat_reply(messages, api_key="key", client_factory=FakeGroq)

    sent = FakeGroq.calls[0]["messages"]
    assert len(sent) == chat.CHAT_HISTORY_LIMIT + 1
    assert sent[1]["content"] == "message 4"
    assert sent[-1]["content"] == "message 9"


@pytest.mark.parametrize("raw,expected", [("5.5", 5.5), ("12", 12.0)])
def test_chat_timeout_reads_the_environment(monkeypatch, raw, expected):
    monkeypatch.setenv("CHAT_TIMEOUT", raw)

    chat.chat_reply(MESSAGES, api_key="key", client_factory=FakeGroq)

    assert FakeGroq.calls[0]["timeout"] == expected


@pytest.mark.parametrize("raw", ["abc", "", "0", "-3"])
def test_invalid_timeout_falls_back_to_default(monkeypatch, raw):
    monkeypatch.setenv("CHAT_TIMEOUT", raw)

    chat.chat_reply(MESSAGES, api_key="key", client_factory=FakeGroq)

    assert FakeGroq.calls[0]["timeout"] == chat.DEFAULT_CHAT_TIMEOUT


def test_blank_completion_is_treated_as_a_failure(caplog):
    FakeGroq.content = "   "

    with caplog.at_level(logging.ERROR):
        response, error = chat.chat_reply(
            MESSAGES, api_key="key", client_factory=FakeGroq
        )

    assert response is None
    assert error == chat.UNAVAILABLE_MESSAGE
    assert "Assistant request failed" in caplog.text


def test_provider_errors_are_not_shown_to_the_user(caplog):
    FakeGroq.error = RuntimeError("invalid api key sk-secret-123")

    with caplog.at_level(logging.ERROR):
        response, error = chat.chat_reply(
            MESSAGES, api_key="key", client_factory=FakeGroq
        )

    assert response is None
    assert error == chat.UNAVAILABLE_MESSAGE
    assert "sk-secret-123" not in error
    assert "sk-secret-123" in caplog.text


def test_reply_is_trimmed():
    FakeGroq.content = "  Use a 330 ohm resistor.  "

    response, _ = chat.chat_reply(MESSAGES, api_key="key", client_factory=FakeGroq)

    assert response == "Use a 330 ohm resistor."
