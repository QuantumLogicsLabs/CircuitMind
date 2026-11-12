"""
CircuitMind - Streamlit Web UI
Monolithic Architecture (Direct Python Imports)
"""

import os
import sys
import json
import base64
import traceback
from dotenv import load_dotenv
import streamlit as st

# Ensure root path is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate.generate import generate_circuit as _generate_circuit
from explain.explain_module import explain_circuit as _explain_circuit
from diagnose.diagnose_module import diagnose_circuit as _diagnose_circuit
from export.export_module import export_module as _export_module
from utils.issue_format import issue_rows

load_dotenv()

# ── API WRAPPER FUNCTIONS (Local) ─────────────────────────────────────────────

def _catch_errors(func, *args, **kwargs):
    try:
        res = func(*args, **kwargs)
        # If the function itself returns an error dict, pass it through
        if isinstance(res, dict) and "error" in res:
            return res
        return res
    except Exception as e:
        return {"error": f"Internal Error: {str(e)}"}

def generate_circuit(prompt):
    return _catch_errors(_generate_circuit, prompt)

def explain_circuit(data):
    return _catch_errors(_explain_circuit, data)

def diagnose_circuit(data):
    return _catch_errors(_diagnose_circuit, data)

def export_module(data, export_format="svg"):
    return _catch_errors(_export_module, data, export_format=export_format)


# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CircuitMind", layout="wide", page_icon="⚡")

st.title("⚡ CircuitMind")
st.subheader("AI-Powered Electronics Assistant")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔧 Generate",
    "📖 Explain",
    "🔍 Diagnose",
    "📤 Export",
    "💬 Chatbot",
])

# ── TAB 1: GENERATE ────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Generate New Circuit")
    prompt = st.text_input("Describe your circuit", "make me a LED circuit")

    if st.button("Generate", type="primary"):
        with st.spinner("Generating..."):
            result = generate_circuit(prompt)

        if not result or "error" in result:
            st.error(result.get("error", "Generation failed"))
        else:
            st.success(f"✅ {result.get('circuit_name', 'Circuit Generated')}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Components:**")
                for c in result.get("components", []):
                    st.markdown(f"- {c}")

            with col2:
                st.markdown("**Connections:**")
                for c in result.get("connections", []):
                    st.markdown(f"- {c}")

            st.caption(
                f"Source: {result.get('source', '')} | Confidence: {result.get('confidence', '')}"
            )

            # ── EXPORT SVG VIA API ──
            svg_res = export_module(json.dumps(result), export_format="svg")

            if svg_res.get("status") == "success" and "svg_markup" in svg_res:
                st.markdown("**Schematic Diagram:**")

                b64 = base64.b64encode(svg_res["svg_markup"].encode()).decode()
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{b64}" '
                    f'style="max-width:400px;width:100%;background:white;padding:16px;border-radius:8px;">',
                    unsafe_allow_html=True,
                )

            st.markdown("**Circuit JSON:**")
            st.code(json.dumps(result, indent=2), language="json")


# ── TAB 2: EXPLAIN ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Explain Circuit")
    json_input = st.text_area("Paste circuit JSON", height=250, key="explain")

    if st.button("Explain", type="primary"):
        try:
            data = json.loads(json_input)

            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]

            result = explain_circuit(data)

            if not result or "error" in result:
                st.error(result.get("error", "Explain failed"))
            else:
                st.success("**Explanation:**")
                st.write(result.get("explanation", "No explanation"))

                if result.get("flow_description"):
                    st.markdown(f"**Flow:** {result['flow_description']}")

                if result.get("component_details"):
                    st.markdown("**Components:**")
                    for comp in result["component_details"]:
                        st.markdown(
                            f"- **{comp['name']}** — {comp['role']}: {comp['description']}"
                        )

                for w in result.get("warnings", []):
                    st.warning(w)

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")


# ── TAB 3: DIAGNOSE ────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Diagnose Circuit")
    json_input2 = st.text_area("Paste circuit JSON", height=200, key="diag")

    if st.button("Diagnose", type="primary"):
        try:
            data = json.loads(json_input2)

            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]

            result = diagnose_circuit(data)

            if not result:
                st.error("Diagnosis failed")
            elif result.get("error"):
                st.error(result["error"])
            elif result.get("passed"):
                st.success("✅ No issues found. Circuit looks valid.")
            else:
                rows = issue_rows(result.get("issues", []))
                st.error(f"❌ {len(rows)} issue(s) found:")
                render = {"error": st.error, "warning": st.warning, "info": st.info}
                for row in rows:
                    render.get(row["severity"], st.info)(row["text"])

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")


# ── TAB 4: EXPORT ──────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Export Circuit")
    json_input3 = st.text_area("Paste circuit JSON", height=200, key="export_area")

    fmt = st.radio("Export Format", ["spice", "svg", "gate_json"], horizontal=True)

    if st.button("Export", type="primary"):
        try:
            data = json.loads(json_input3)

            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]

            result = export_module(json.dumps(data), export_format=fmt)

            st.session_state["export_result"] = result
            st.session_state["export_format"] = fmt

        except json.JSONDecodeError as e:
            st.session_state["export_result"] = {
                "status": "error",
                "message": f"Invalid JSON: {e}",
            }

    if "export_result" in st.session_state:
        result = st.session_state["export_result"]
        fmt_used = st.session_state.get("export_format", "spice")

        if result.get("error") or result.get("status") == "error":
            message = result.get("error") or result.get("message") or "Export request failed"
            st.error(message)
        else:
            st.json(result)

            if fmt_used == "spice" and "spice_netlist" in result:
                st.download_button(
                    label="⬇️ Download SPICE File",
                    data=result["spice_netlist"],
                    file_name="circuit.sp",
                    mime="text/plain",
                )

            elif fmt_used == "svg" and "svg_markup" in result:
                b64 = base64.b64encode(result["svg_markup"].encode()).decode()
                st.markdown(
                    f'<img src="data:image/svg+xml;base64,{b64}" '
                    f'style="max-width:400px;width:100%;background:white;padding:16px;border-radius:8px;">',
                    unsafe_allow_html=True,
                )

                st.download_button(
                    label="⬇️ Download SVG File",
                    data=result["svg_markup"],
                    file_name=f"{result.get('circuit_name', 'circuit').replace(' ', '_')}.svg",
                    mime="image/svg+xml",
                )


# ── TAB 5: CHATBOT ─────────────────────────────────────────────────────────────
with tab5:
    st.subheader("💬 CircuitMind Assistant")
    st.write("Ask me anything about circuits or electronics!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm CircuitMind Assistant. Ask me anything about circuits or electronics! 😊",
            }
        ]

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm CircuitMind Assistant. Ask me anything about circuits or electronics! 😊",
            }
        ]
        st.rerun()

    chat_container = st.container(height=450)

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    user_input = st.chat_input("Ask about any circuit or electronics topic...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            response = "⚠️ GROQ_API_KEY not set. Please add it to your .env file."
        else:
            try:
                from groq import Groq

                client = Groq(api_key=api_key)

                system_msg = {
                    "role": "system",
                    "content": (
                        "You are CircuitMind Assistant — an expert AI for electronics and circuits. "
                        "Help users understand components, design circuits, explain how circuits work, "
                        "and diagnose problems. Keep answers clear, helpful, and concise."
                    ),
                }

                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[-6:]
                ]

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[system_msg] + history,
                    max_tokens=500,
                )

                response = completion.choices[0].message.content

            except Exception as e:
                response = f"Sorry, I couldn't connect right now. Error: {e}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ CircuitMind")
    st.markdown("AI-powered electronics assistant")
    st.caption("Built by Team Delta")

st.caption("CircuitMind Project")