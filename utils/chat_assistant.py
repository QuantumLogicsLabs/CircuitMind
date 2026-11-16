"""
CircuitMind - Assistant Chat Helper
utils/chat_assistant.py

Builds one chat turn for the Streamlit assistant. Kept outside
app_streamlit.py so request shaping, timeouts and failure handling can be
tested without importing Streamlit.
"""

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_CHAT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_CHAT_TIMEOUT = 30.0
CHAT_MAX_TOKENS = 500
CHAT_HISTORY_LIMIT = 6

SYSTEM_PROMPT = (
    "You are CircuitMind Assistant — an expert AI for electronics and circuits. "
    "Help users understand components, design circuits, explain how circuits work, "
    "and diagnose problems. Keep answers clear, helpful, and concise."
)

MISSING_KEY_MESSAGE = (
    "⚠️ GROQ_API_KEY not set. Please add it to your .env file."
)
UNAVAILABLE_MESSAGE = (
    "Sorry, I couldn't reach the assistant right now. Please try again."
)


def _chat_timeout() -> float:
    """Chat request timeout in seconds, overridable via CHAT_TIMEOUT."""
    raw = os.environ.get("CHAT_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_CHAT_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        logger.warning("Ignoring invalid CHAT_TIMEOUT=%r", raw)
        return DEFAULT_CHAT_TIMEOUT
    if value <= 0:
        logger.warning("Ignoring non-positive CHAT_TIMEOUT=%r", raw)
        return DEFAULT_CHAT_TIMEOUT
    return value


def _default_client(api_key: str):
    from groq import Groq

    return Groq(api_key=api_key)


def build_history(messages: list[dict]) -> list[dict]:
    """Return the last few turns in the shape the chat API expects."""
    return [
        {"role": message["role"], "content": message["content"]}
        for message in messages[-CHAT_HISTORY_LIMIT:]
    ]


def chat_reply(
    messages: list[dict],
    api_key: str | None = None,
    client_factory=None,
) -> tuple[str | None, str | None]:
    """Return ``(response, error)`` for one assistant turn.

    ``error`` is safe to display: the underlying exception is only logged, so
    provider messages or keys never reach the browser.
    """
    if api_key is None:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return None, MISSING_KEY_MESSAGE

    factory = client_factory or _default_client

    try:
        client = factory(api_key)
        completion = client.chat.completions.create(
            model=DEFAULT_CHAT_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
            + build_history(messages),
            max_tokens=CHAT_MAX_TOKENS,
            timeout=_chat_timeout(),
        )
        content = completion.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("assistant returned an empty message")
        return content.strip(), None
    except Exception:
        logger.exception("Assistant request failed")
        return None, UNAVAILABLE_MESSAGE
