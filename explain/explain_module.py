"""
CircuitMind AI — Explain Module
================================
Author  : Mustehsan Kazmi
Module  : Circuit-to-Text Explainer (NLP Sub-Module)
Pipeline: JSON → [Analyzer Agent] → [Writer Agent] → Plain-English / Expert Description

Strategy: Multi-Agent Prompt System using Groq API (no fine-tuning required).
          Two chained LLM agents:
            Agent 1 — Circuit Analyzer  : extracts key facts from the JSON (components,
                                          connections, topology, potential issues).
            Agent 2 — Explanation Writer: takes those facts and writes a graded explanation
                                          (beginner / intermediate / expert).

How to plug into the pipeline:
    from explain_module import explain_circuit
    result = explain_circuit(circuit_json, level="beginner")   # or "expert"

No changes needed to this file once you set the env variable:
    export GROQ_API_KEY="your_key_here"          # preferred (free & fast)
    export OPENAI_API_KEY="your_key_here"        # fallback
"""

import os
import json
import textwrap
from typing import Literal


# pip install groq         free tier, very fast


try:
    from groq import Groq
    _CLIENT_TYPE = "groq"
    _client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    _MODEL = "llama-3.1-8b-instant"          # free, fast, 8B context
except ImportError:
    try:
        from openai import OpenAI
        _CLIENT_TYPE = "openai"
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        _MODEL = "gpt-3.5-turbo"
    except ImportError:
        raise ImportError(
            "Install either 'groq' or 'openai':\n"
            "  pip install groq\n"
            "  pip install openai"
        )

# ─────────────────────────────────────────────────────────────────────────────
# AGENT PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

_ANALYZER_SYSTEM = textwrap.dedent("""
    You are a circuit analysis engine. Your ONLY job is to read a circuit JSON
    and produce a structured analysis object — nothing else.

    The JSON follows this schema:
      {
        "components": [
          { "id": str, "type": str, "value": str|null, "label": str|null }
        ],
        "connections": [
          { "from": str, "to": str, "wire_id": str }
        ],
        "metadata": { ... }   <- optional
      }

    Respond ONLY with a JSON object in this exact shape (no markdown, no extra text):
    {
      "component_summary": "...",
      "connection_summary": "...",
      "topology_type": "series | parallel | series-parallel | bridge | unknown",
      "power_source": "...",
      "load_components": [...],
      "control_components": [...],
      "likely_purpose": "...",
      "beginner_key_points": ["...", "...", "..."],
      "expert_key_points": ["...", "...", "..."],
      "potential_issues": ["..."]
    }
""").strip()

_ANALYZER_USER_TMPL = "Analyze this circuit JSON:\n\n{circuit_json}"

# ── Writer prompts per level ──────────────────────────────────────────────────

_WRITER_SYSTEM_BEGINNER = textwrap.dedent("""
    You are a friendly electronics teacher writing for a student who has NEVER
    studied circuits. Use simple, everyday language. No equations. No jargon.
    If you must use a technical word, explain it immediately in parentheses.

    Write 3–5 short paragraphs:
      1. What this circuit does (one sentence).
      2. What each main component does (plain language).
      3. How electricity flows through the circuit step-by-step.
      4. A real-life analogy to make it intuitive.
      5. Safety or practical tip (if relevant).

    Tone: warm, encouraging, clear.
""").strip()

_WRITER_SYSTEM_INTERMEDIATE = textwrap.dedent("""
    You are an electronics instructor writing for a second-year engineering student.
    Use standard technical terminology but keep explanations concise.

    Write 4–6 paragraphs covering:
      1. Circuit purpose and classification (series/parallel/etc.).
      2. Role of each component with typical values.
      3. Current path and voltage distribution.
      4. Any notable design choices or trade-offs.
      5. Common failure modes or things to watch.

    Tone: professional, educational, direct.
""").strip()

_WRITER_SYSTEM_EXPERT = textwrap.dedent("""
    You are a senior electronics engineer writing a technical review for a peer.
    Use precise terminology. Include equations where appropriate (use plain-text
    notation, e.g. V = IR, P = V²/R). Be analytical, not descriptive.

    Cover:
      1. Topology classification and why it matters here.
      2. Quantitative analysis: KVL/KCL equations, voltage divider ratios,
         current limiting, power dissipation estimates.
      3. Component selection rationale (tolerances, ratings).
      4. Potential failure modes, fault analysis, edge cases.
      5. Suggested improvements or alternative topologies.

    Tone: technical, concise, peer-level.
""").strip()

_WRITER_USER_TMPL = textwrap.dedent("""
    Using the circuit analysis below, write a {level} explanation of the circuit.

    ANALYSIS:
    {analysis_json}
""").strip()

_LEVEL_TO_SYSTEM = {
    "beginner":     _WRITER_SYSTEM_BEGINNER,
    "intermediate": _WRITER_SYSTEM_INTERMEDIATE,
    "expert":       _WRITER_SYSTEM_EXPERT,
}

# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _chat(system: str, user: str, temperature: float = 0.3) -> str:
    """Single LLM call — works for both Groq and OpenAI clients."""
    response = _client.chat.completions.create(
        model=_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def _run_analyzer_agent(circuit_json: dict) -> dict:
    """
    Agent 1 — Circuit Analyzer.
    Takes raw circuit JSON → returns structured analysis dict.
    """
    user_msg = _ANALYZER_USER_TMPL.format(
        circuit_json=json.dumps(circuit_json, indent=2)
    )
    raw = _chat(_ANALYZER_SYSTEM, user_msg, temperature=0.1)

    # Strip accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Graceful fallback — return raw text wrapped in a dict
        return {"raw_analysis": raw}


def _run_writer_agent(
    analysis: dict,
    level: Literal["beginner", "intermediate", "expert"]
) -> str:
    """
    Agent 2 — Explanation Writer.
    Takes structured analysis dict + level → returns final explanation string.
    """
    system = _LEVEL_TO_SYSTEM.get(level, _WRITER_SYSTEM_BEGINNER)
    user_msg = _WRITER_USER_TMPL.format(
        level=level,
        analysis_json=json.dumps(analysis, indent=2)
    )
    return _chat(system, user_msg, temperature=0.6)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def explain_circuit(
    circuit_json: dict,
    level: Literal["beginner", "intermediate", "expert"] = "beginner",
    return_analysis: bool = False,
) -> dict:
    """
    Main entry point for the Explain Module.

    Parameters
    ----------
    circuit_json  : dict   — Standard CircuitMind JSON (components + connections).
    level         : str    — "beginner" | "intermediate" | "expert"
    return_analysis: bool  — If True, also return the intermediate analysis object.

    Returns
    -------
    {
      "level":       str,
      "explanation": str,
      "analysis":    dict   <- only if return_analysis=True
    }

    Example
    -------
    from explain_module import explain_circuit

    with open("circuit.json") as f:
        data = json.load(f)

    result = explain_circuit(data, level="expert")
    print(result["explanation"])
    """
    if not isinstance(circuit_json, dict):
        raise TypeError("circuit_json must be a Python dict.")

    if level not in ("beginner", "intermediate", "expert"):
        raise ValueError("level must be 'beginner', 'intermediate', or 'expert'.")

    # ── Agent 1 ────────────────────────────────────────────────────────────
    analysis = _run_analyzer_agent(circuit_json)

    # ── Agent 2 ────────────────────────────────────────────────────────────
    explanation = _run_writer_agent(analysis, level)

    result = {
        "level":       level,
        "explanation": explanation,
    }
    if return_analysis:
        result["analysis"] = analysis

    return result
