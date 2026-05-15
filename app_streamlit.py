
import sys
import os
import json
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module

st.set_page_config(page_title="CircuitMind", layout="wide", page_icon="⚡")
st.title("⚡ CircuitMind")
st.subheader("AI-Powered Electronics Assistant")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔧 Generate",
    "📖 Explain",
    "🔍 Diagnose",
    "📤 Export",
    "💬 Chatbot"
])

# ── TAB 1: GENERATE ──────────────────────────────────
with tab1:
    st.subheader("Generate New Circuit")
    prompt = st.text_input("Describe your circuit", "make me a LED circuit")
    if st.button("Generate", type="primary"):
        with st.spinner("Generating..."):
            result = generate_circuit(prompt)
        if "error" in result:
            st.error(result["error"])
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
            st.caption(f"Source: {result.get('source','')} | Confidence: {result.get('confidence','')}")
            st.json(result)

# ── TAB 2: EXPLAIN ───────────────────────────────────
with tab2:
    st.subheader("Explain Circuit")
    json_input = st.text_area("Paste circuit JSON", height=250, key="explain")
    if st.button("Explain", type="primary"):
        try:
            data = json.loads(json_input)
            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]
            result = explain_circuit(data)
            st.success("**Explanation:**")
            st.write(result.get("explanation", "No explanation"))
            if result.get("flow_description"):
                st.markdown(f"**Flow:** {result['flow_description']}")
            if result.get("component_details"):
                st.markdown("**Components:**")
                for comp in result["component_details"]:
                    st.markdown(f"- **{comp['name']}** — {comp['role']}: {comp['description']}")
            if result.get("warnings"):
                for w in result["warnings"]:
                    st.warning(w)
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

# ── TAB 3: DIAGNOSE ──────────────────────────────────
with tab3:
    st.subheader("Diagnose Circuit")
    json_input2 = st.text_area("Paste circuit JSON", height=200, key="diag")
    if st.button("Diagnose", type="primary"):
        try:
            data = json.loads(json_input2)
            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]
            result = diagnose_circuit(data)
            if result["passed"]:
                st.success("✅ No issues found! Circuit looks valid.")
            else:
                st.error(f"❌ {len(result['issues'])} issue(s) found:")
                for issue in result["issues"]:
                    if issue.startswith("Error"):
                        st.error(issue)
                    elif issue.startswith("Warning"):
                        st.warning(issue)
                    else:
                        st.info(issue)
        except Exception as e:
            st.error(f"Invalid JSON: {e}")

# ── TAB 4: EXPORT ────────────────────────────────────
with tab4:
    st.subheader("Export Circuit")
    json_input3 = st.text_area("Paste circuit JSON", height=200, key="export_area")
    fmt = st.radio("Export Format", ["spice", "svg"], horizontal=True)
    if st.button("Export", type="primary"):
        try:
            data = json.loads(json_input3)
            if isinstance(data, dict) and "circuit_json" in data:
                data = data["circuit_json"]
            result = export_module(json.dumps(data), export_format=fmt, save_to_file=True)
            st.json(result)
            if fmt == "spice":
                st.download_button(
                    label="⬇️ Download SPICE File",
                    data=result.get("spice_netlist", ""),
                    file_name="circuit.sp",
                    mime="text/plain"
                )
            elif fmt == "svg" and "svg_file" in result:
                try:
                    with open(result["svg_file"], "rb") as f:
                        st.download_button(
                            label="⬇️ Download SVG File",
                            data=f,
                            file_name=result["svg_file"],
                            mime="image/svg+xml"
                        )
                except:
                    st.info("SVG file generated. Check your folder.")
        except Exception as e:
            st.error(f"Error: {e}")

# ── TAB 5: CHATBOT ───────────────────────────────────
with tab5:
    st.subheader("💬 CircuitMind Assistant")
    st.write("Ask me anything about circuits or electronics!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm CircuitMind Assistant. Ask me anything about circuits or electronics! 😊"}
        ]

    # Clear chat button - top pe
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm CircuitMind Assistant. Ask me anything about circuits or electronics! 😊"}
        ]
        st.rerun()

    # Chat container - fixed height, scrollable
    chat_container = st.container(height=450)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Input box - always at bottom
    user_input = st.chat_input("Ask about any circuit or electronics topic...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            from groq import Groq
            api_key = os.environ.get("GROQ_API_KEY")

            if not api_key:
                response = "GROQ_API_KEY not set. Please add it to your .env file."
            else:
                client = Groq(api_key=api_key)
                groq_messages = [
                    {
                        "role": "system",
                        "content": """You are CircuitMind Assistant — an expert AI for electronics and circuits.
You help users with:
- Understanding electronic components (resistors, LEDs, capacitors, transistors, etc.)
- Circuit design and connections
- Explaining how circuits work
- Diagnosing circuit problems

This app has 4 modules:
1. Generate — converts text to circuit JSON
2. Explain — explains circuit JSON in plain English
3. Diagnose — finds electrical issues in circuits
4. Export — exports to SPICE or SVG format

Keep answers clear, helpful, and concise."""
                    }
                ]
                for msg in st.session_state.messages[-6:]:
                    groq_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_messages,
                    max_tokens=500
                )
                response = completion.choices[0].message.content

        except Exception as e:
            response = f"Sorry, I couldn't connect right now. Error: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ CircuitMind")
    st.markdown("AI-powered electronics assistant")
    st.caption("Built by Team Delta")

st.caption("CircuitMind Project")
