
#Streamlit UI EasyF1
import streamlit as st
import engine

# Page config
st.set_page_config(
    page_title="EasyF1 — Race Strategy Assistant",
    page_icon="🏎️",
    layout="wide"
)

# Header
st.title("🏎️ EasyF1")
st.caption("An Agentic RAG system for F1 race strategy — comparing two LLMs on historical data")

# Loading circuits once
@st.cache_data
def load_circuits():
    return engine.list_circuits()

circuits = load_circuits()

# Sidebar — scenario builder
with st.sidebar:
    st.header("Build Your Scenario")

    circuit = st.selectbox(
        "Circuit",
        options=circuits,
        index=circuits.index("Silverstone") if "Silverstone" in circuits else 0,
        help="Type to search — e.g. 'Sil' finds Silverstone"
    )

    total_laps = st.number_input("Total race laps", min_value=20, max_value=78, value=52)
    current_lap = st.slider("Current lap", min_value=1, max_value=int(total_laps), value=min(32, int(total_laps)))

    driver = st.text_input("Driver (optional)", value="", placeholder="e.g. Hamilton")

    col1, col2 = st.columns(2)
    with col1:
        position = st.selectbox("Position", [f"P{i}" for i in range(1, 21)], index=3)
    with col2:
        tyre = st.selectbox("Current tyre", ["Soft", "Medium", "Hard", "Intermediate", "Wet"], index=2)

    tyre_age = st.slider("Tyre age (laps)", min_value=0, max_value=50, value=25)

    safety_car = st.checkbox("Safety Car deployed")

    st.divider()
    run = st.button("🏁 Get Strategy", type="primary", use_container_width=True)


# Building the scenario sentence from inputs
def build_scenario():
    driver_part = f"{driver} is" if driver.strip() else "A driver is"
    sc_part = " A Safety Car has just been deployed." if safety_car else ""
    return (
        f"It's lap {current_lap} of {total_laps} at {circuit}. "
        f"{driver_part} running {position} on {tyre_age}-lap-old {tyre.lower()} tyres."
        f"{sc_part} What is the optimal strategy from here?"
    )


#main area - results 
if run:
    scenario = build_scenario()

    st.subheader("Scenario")
    st.info(scenario)

    with st.spinner("Consulting historical data and both models... (Nemotron can take ~20s)"):
        result = engine.compare(scenario, circuit=circuit)

    # Show retrieved context in an expander
    with st.expander(f"📚 Historical context retrieved ({len(result['context'])} chunks)"):
        for c in result['context']:
            st.text(f"• {c}")

    # comparsion of models (side by side)
    st.subheader("Strategy Recommendations")
    col_a, col_b = st.columns(2)

    def render_recommendation(raw_text):
        """Display a parsed recommendation with aligned, fixed-height fields."""
        parsed = engine.parse_recommendation(raw_text)

        # Fallback: if nothing parsed, show raw and stop
        if not any(parsed.values()):
            st.markdown(raw_text)
            return

        # (label, content, fixed height in px) — heights chosen so
        # both columns' labels line up regardless of content length
        rows = [
            ("Verdict",    parsed['VERDICT'],    60),
            ("Confidence", parsed['CONFIDENCE'],  60),
            ("Reasoning",  parsed['REASONING'],  220),
            ("Risk",       parsed['RISK'],       160),
        ]

        for label, content, height in rows:
            st.markdown(f"**{label}**")
            box = st.container(height=height, border=False)
            box.markdown(content if content else "—")

    with col_a:
        st.markdown("### 🔵 Gemini 2.5 Flash-Lite")
        st.caption("Google · proprietary")
        render_recommendation(result['gemini'])

    with col_b:
        st.markdown("### 🟢 Nemotron 3 Ultra 550B")
        st.caption("NVIDIA · open-weight")
        render_recommendation(result['nemotron'])