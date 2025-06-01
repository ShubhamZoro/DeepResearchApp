import streamlit as st
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from research_manager import ResearchManager

# Enable nested asyncio loop support for Streamlit
nest_asyncio.apply()

# Load environment variables
load_dotenv(override=True)

st.set_page_config(page_title="Deep Research", layout="centered")

# Title
st.title("🔍 Deep Research")

# Input
query = st.text_input("What topic would you like to research?", "")

# Submit button
if st.button("Run") and query:
    # Place where output will appear
    placeholder = st.empty()

    async def run(query):
        output = ""
        async for chunk in ResearchManager().run(query):
            output += chunk
            placeholder.markdown(output)

    # Run the async function within Streamlit
    asyncio.run(run(query))
