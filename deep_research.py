import streamlit as st
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from research_manager import ResearchManager
from chat_db import init_db, start_session, save_message, get_chat_history

# Setup
nest_asyncio.apply()
load_dotenv(override=True)
st.set_page_config(page_title="Deep Research", layout="centered")
st.title("🔍 Deep Research")

# Init DB and Session
init_db()
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.query = ""
    st.session_state.clarification = ""
    st.session_state.session_id = start_session()

manager = ResearchManager()

# Step 1: Ask for research topic
if st.session_state.step == 1:
    query = st.text_input("What topic would you like to research?", "")
    if st.button("Next") and query:
        st.session_state.query = query
        save_message(st.session_state.session_id, "user", query)
        st.session_state.step = 2
        st.rerun()

# Step 2: Clarify
elif st.session_state.step == 2:
    prompt_html = """
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;">
        Could you please clarify what you're looking for regarding your topic?
        Are you interested in specific tools, building one yourself, or understanding capabilities?
        Also, what features or use cases are most important to you?
    </div>
    """
    st.markdown(prompt_html, unsafe_allow_html=True)

    clarification = st.text_input("Your clarification:")

    if st.button("Submit Clarification") and clarification:
        st.session_state.clarification = clarification
        save_message(st.session_state.session_id, "user", clarification)
        st.session_state.step = 3
        st.rerun()

# Step 3: Run full pipeline
elif st.session_state.step == 3:
    st.markdown("### ⏳ Running full research based on your input...")
    placeholder = st.empty()

    full_query = f"{st.session_state.query}\n\nUser clarification:\n{st.session_state.clarification}"

    async def run(query):
        output = ""
        async for chunk in manager.run(query):
            output += chunk + "\n\n"
            placeholder.markdown(output)
        save_message(st.session_state.session_id, "assistant", output)

    asyncio.run(run(full_query))

    st.markdown("### 🤔 Want to refine the report or ask something else?")
    followup = st.text_input("Add a clarification or ask a related question:", key="followup_input")
    if st.button("Submit Follow-up") and followup:
        save_message(st.session_state.session_id, "user", followup)
        st.session_state.query = followup
        st.session_state.step = 2  # Go back to clarification stage
        st.rerun()

    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()

# Optional: Show chat history
with st.expander("🗂️ Show Chat History"):
    history = get_chat_history(st.session_state.session_id)
    for role, msg in history:
        st.markdown(f"**{role.capitalize()}:** {msg}")
