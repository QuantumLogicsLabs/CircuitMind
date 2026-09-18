"""
CircuitMind - Hint Module
hint/hint_module.py

Given a digital-logic problem (truth table, required I/O ports) and a
student's current — possibly incomplete or wrong — gate/wire graph, returns
one short, non-spoiler hint nudging them toward the fix.
Strategy: LLM (Groq) first -> rule-based fallback if unavailable.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── LLM Hint ─────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a digital logic design tutor. A student is building a combinational "
    "or sequential logic circuit (gate types: AND, OR, NOT, NAND, NOR, XOR, XNOR, "
    "INPUT, OUTPUT, BUFFER) in a visual circuit builder, trying to match a truth "
    "table. You will be given the problem, its truth table, the student's CURRENT "
    "circuit graph (gates + wires), and, if available, which rows their last "
    "submit attempt failed.\n\n"
    "The student may also ask what circuit they have created. When they ask for "
    "the circuit name, identify the circuit from the problem information and the "
    "current gate/wire structure. Give the circuit name directly and briefly "
    "explain the evidence from the circuit. Do not invent a circuit name when the "
    "available information is insufficient.\n\n"
    "For normal hint requests, reply with exactly ONE short hint (2-4 sentences, "
    "plain English) that nudges the student toward the fix. Point at the kind of "
    "mistake or the next concept to apply — do NOT give the full gate list, wiring "
    "diagram, or a complete boolean expression that hands them the answer. Be "
    "specific to what you see in their current circuit, not generic textbook text."
)


def _summarize_circuit(gates: list, wires: list) -> str:
    if not gates:
        return "The canvas is empty — no gates placed yet."

    gate_lines = []
    for g in gates:
        name = g.get("label") or f"gate{g.get('id')}"
        gate_lines.append(f"- {name}: type={g.get('type')}")

    wire_lines = []
    for w in wires or []:
        from_g = next((g for g in gates if g.get("id") == w.get("fromId")), None)
        to_g = next((g for g in gates if g.get("id") == w.get("toId")), None)
        if from_g and to_g:
            wire_lines.append(f"- {from_g.get('label')} -> {to_g.get('label')}")

    return (
        "Gates:\n" + "\n".join(gate_lines)
        + "\n\nWires:\n" + ("\n".join(wire_lines) or "(none)")
    )


def _build_user_prompt(payload: dict) -> str:
    inputs = payload.get("inputs", [])
    outputs = payload.get("outputs", [])
    truth_table = payload.get("truth_table", [])
    last_result = payload.get("last_result") or {}

    parts = [
        f"Problem: {payload.get('problem_title', 'Untitled problem')}",
        f"Description: {payload['problem_description']}" if payload.get("problem_description") else "",
        f"Inputs: {', '.join(inputs)}",
        f"Outputs: {', '.join(outputs)}",
        f"Truth table (JSON, first 16 rows): {json.dumps(truth_table[:16])}",
        "",
        "Student's current circuit:",
        _summarize_circuit(payload.get("gates", []), payload.get("wires", [])),
    ]

    failing_rows = last_result.get("failing_rows") or []
    if last_result.get("error"):
        parts.append(f"\nLast submit attempt error: {last_result['error']}")
    elif failing_rows:
        parts.append(
            f"\nLast submit attempt: {len(failing_rows)} row(s) failed: "
            f"{json.dumps(failing_rows[:5])}"
        )
    elif last_result.get("passed"):
        parts.append(
            "\nLast submit attempt passed — the student may be asking for a "
            "refinement or a different angle, not a basic fix."
        )

    return "\n".join(p for p in parts if p)

def _identify_circuit(payload: dict) -> str:
    """Identify a common digital circuit from its problem data and gate graph."""
    title = (payload.get("problem_title") or "").strip()
    description = (payload.get("problem_description") or "").strip()
    text = f"{title} {description}".lower()

    known_circuits = {
        "half adder": "Half Adder",
        "full adder": "Full Adder",
        "half subtractor": "Half Subtractor",
        "full subtractor": "Full Subtractor",
        "multiplexer": "Multiplexer",
        "mux": "Multiplexer",
        "demultiplexer": "Demultiplexer",
        "demux": "Demultiplexer",
        "decoder": "Decoder",
        "encoder": "Encoder",
        "comparator": "Comparator",
    }

    for keyword, circuit_name in known_circuits.items():
        if keyword in text:
            return circuit_name

    gates = payload.get("gates", [])
    gate_types = [str(g.get("type", "")).upper() for g in gates]

    input_count = sum(gate_type == "INPUT" for gate_type in gate_types)
    output_count = sum(gate_type == "OUTPUT" for gate_type in gate_types)

    logic_types = [
        gate_type for gate_type in gate_types
        if gate_type not in {"INPUT", "OUTPUT", "BUFFER"}
    ]

    if input_count == 2 and output_count == 2:
        if "XOR" in logic_types and "AND" in logic_types:
            return "Half Adder"

    return title or "Unknown circuit"

def _hint_with_llm(payload: dict) -> str:
    if not GROQ_AVAILABLE:
        raise RuntimeError("Groq not installed. Run: pip install groq")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(payload)},
        ],
        max_tokens=220,
        temperature=0.4,
    )
    return completion.choices[0].message.content.strip()


# ── Rule-Based Fallback ────────────────────────────────────────────────────────

def _hint_with_rules(payload: dict) -> str:
    gates = payload.get("gates", [])
    wires = payload.get("wires", [])
    inputs = payload.get("inputs", [])
    outputs = payload.get("outputs", [])

    if not gates:
        return (
            f"Start by placing {len(inputs)} INPUT gate(s) named exactly "
            f"{', '.join(inputs) or '(see problem)'} and {len(outputs)} OUTPUT "
            f"gate(s) named {', '.join(outputs) or '(see problem)'} — then wire "
            "logic gates between them."
        )

    input_gates = [g for g in gates if g.get("type") == "INPUT"]
    output_gates = [g for g in gates if g.get("type") == "OUTPUT"]
    if len(input_gates) < len(inputs) or len(output_gates) < len(outputs):
        return (
            f"Your circuit has {len(input_gates)} INPUT and {len(output_gates)} "
            f"OUTPUT gate(s), but this problem needs {len(inputs)} and "
            f"{len(outputs)}. Add the missing ones and label them to match."
        )

    wired_ids = {w.get("fromId") for w in wires} | {w.get("toId") for w in wires}
    floating = [g for g in gates if g.get("id") not in wired_ids]
    if floating:
        names = ", ".join(g.get("label", "?") for g in floating)
        return (
            f"'{names}' isn't connected to anything yet — a floating gate can't "
            "affect the output. Wire it in."
        )

    return (
        "Gate and wire counts look reasonable — walk through the truth table row "
        "by row and check whether your gate types (AND/OR/XOR/NOT) match what "
        "each row actually needs on the path from input to output."
    )


# ── Public API ────────────────────────────────────────────────────────────────

def generate_hint(payload: dict) -> dict:
    """
    Main entry point.

    Supports:
    - normal hint requests
    - circuit identification requests

    Output:
    {
        "hint": str,
        "source": "llm" | "rule-based"
    }
    """
    if payload.get("request_type") == "identify":
        circuit_name = _identify_circuit(payload)

        if circuit_name != "Unknown circuit":
            return {
                "hint": f"You have created a {circuit_name} circuit.",
                "source": "rule-based",
                "circuit_name": circuit_name,
            }

    try:
        hint_text = _hint_with_llm(payload)
        source = "llm"
    except Exception as e:
        logger.warning(
            f"LLM hint unavailable ({e}), falling back to rule-based hint"
        )
        hint_text = _hint_with_rules(payload)
        source = "rule-based"

    return {"hint": hint_text, "source": source}