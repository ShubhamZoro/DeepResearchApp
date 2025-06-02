import streamlit as st
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from research_manager import ResearchManager
from chat_db import (
    init_db, start_session, save_message, get_chat_history, 
    get_all_sessions, update_session_name, delete_session, get_session_name
)
from datetime import datetime

# Setup
nest_asyncio.apply()
load_dotenv(override=True)
st.set_page_config(page_title="Deep Research", layout="wide")

# Init DB
init_db()

# Initialize session state
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "research_step" not in st.session_state:
    st.session_state.research_step = 1
if "query" not in st.session_state:
    st.session_state.query = ""
if "clarification" not in st.session_state:
    st.session_state.clarification = ""

manager = ResearchManager()

# Sidebar for session management
with st.sidebar:
    st.title("💬 Chat Sessions")
    
    # New session button
    if st.button("➕ New Session", use_container_width=True):
        new_session_id = start_session()
        st.session_state.current_session_id = new_session_id
        st.session_state.research_step = 1
        st.session_state.query = ""
        st.session_state.clarification = ""
        st.rerun()
    
    st.divider()
    
    # Display all sessions
    sessions = get_all_sessions()
    
    if sessions:
        st.subheader("Previous Sessions")
        for session_id, session_name, created_at, last_message_at in sessions:
            # Create a container for each session
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Session button
                    if st.button(
                        f"📝 {session_name}", 
                        key=f"session_{session_id}",
                        use_container_width=True,
                        type="primary" if st.session_state.current_session_id == session_id else "secondary"
                    ):
                        st.session_state.current_session_id = session_id
                        st.session_state.research_step = 4  # Go to chat mode
                        st.rerun()
                
                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{session_id}", help="Delete session"):
                        delete_session(session_id)
                        if st.session_state.current_session_id == session_id:
                            st.session_state.current_session_id = None
                            st.session_state.research_step = 1
                        st.rerun()
                
                # Show last message time
                try:
                    last_msg_time = datetime.fromisoformat(last_message_at.replace('Z', '+00:00'))
                    st.caption(f"Last activity: {last_msg_time.strftime('%Y-%m-%d %H:%M')}")
                except:
                    st.caption(f"Created: {created_at}")
                
                st.divider()

# Main content area
if st.session_state.current_session_id is None:
    # No session selected, show welcome screen
    st.title("🔍 Deep Research")
    st.markdown("""
    Welcome to Deep Research! This tool helps you conduct comprehensive research on any topic.
    
    **To get started:**
    1. Click "➕ New Session" in the sidebar to create a new research session
    2. Or select an existing session from the sidebar to continue a previous conversation
    
    **Features:**
    - Multi-step research process with AI agents
    - Web search and analysis
    - Comprehensive report generation
    - Email delivery of results
    - Session-based chat history
    """)

else:
    # Session is selected
    current_session_name = get_session_name(st.session_state.current_session_id)
    st.title(f"🔍 {current_session_name}")
    
    # Research steps (1-3) or Chat mode (4)
    if st.session_state.research_step == 1:
        # Step 1: Ask for research topic
        st.subheader("Step 1: Research Topic")
        query = st.text_input("What topic would you like to research?", value=st.session_state.query)
        
        if st.button("Next") and query:
            st.session_state.query = query
            save_message(st.session_state.current_session_id, "user", query)
            # Update session name with the query
            session_name = f"Research: {query[:50]}..." if len(query) > 50 else f"Research: {query}"
            update_session_name(st.session_state.current_session_id, session_name)
            st.session_state.research_step = 2
            st.rerun()
    
    elif st.session_state.research_step == 2:
        # Step 2: Clarify
        st.subheader("Step 2: Clarification")
        
        prompt_html = """
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
            Could you please clarify what you're looking for regarding your topic?
            Are you interested in specific tools, building one yourself, or understanding capabilities?
            Also, what features or use cases are most important to you?
        </div>
        """
        st.markdown(prompt_html, unsafe_allow_html=True)
        
        clarification = st.text_input("Your clarification:", value=st.session_state.clarification)
        
        if st.button("Submit Clarification") and clarification:
            st.session_state.clarification = clarification
            save_message(st.session_state.current_session_id, "user", clarification)
            st.session_state.research_step = 3
            st.rerun()
    
    elif st.session_state.research_step == 3:
        # Step 3: Run full pipeline
        st.subheader("Step 3: Running Research")
        st.markdown("### ⏳ Running full research based on your input...")
        
        placeholder = st.empty()
        
        full_query = f"{st.session_state.query}\n\nUser clarification:\n{st.session_state.clarification}"
        
        async def run(query):
            output = ""
            async for chunk in manager.run(query):
                output += chunk + "\n\n"
                placeholder.markdown(output)
            save_message(st.session_state.current_session_id, "assistant", output)
            st.session_state.research_step = 4  # Move to chat mode
            st.rerun()
        
        # Run the research
        asyncio.run(run(full_query))
    
    elif st.session_state.research_step == 4:
        # Chat mode - show all messages and allow new questions
        st.subheader("Chat History & Continue Conversation")
        
        # Display chat history
        chat_history = get_chat_history(st.session_state.current_session_id)
        
        # Create a scrollable container for chat history
        chat_container = st.container()
        
        with chat_container:
            for role, content, timestamp in chat_history:
                if role == "user":
                    with st.chat_message("user"):
                        st.write(content)
                else:
                    with st.chat_message("assistant"):
                        st.write(content)
        
        st.divider()
        
        # Input for new questions
        st.subheader("Ask a Follow-up Question")
        
        # Create a form for the chat input
        with st.form("chat_form", clear_on_submit=True):
            new_question = st.text_area(
                "Continue the conversation:",
                placeholder="Ask a follow-up question, request clarification, or start a new research topic...",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submit_chat = st.form_submit_button("Send Message", use_container_width=True)
            
            with col2:
                submit_research = st.form_submit_button("New Research", use_container_width=True, type="secondary")
        
        # Handle form submissions
        if submit_chat and new_question:
            # Save user message
            save_message(st.session_state.current_session_id, "user", new_question)
            
            # Simple response for follow-up (you can enhance this with more sophisticated logic)
            st.session_state.query = new_question
            st.session_state.clarification = ""
            
            # Check if this looks like a new research request
            research_keywords = ["research", "analyze", "study", "investigate", "explore", "find information about"]
            if any(keyword in new_question.lower() for keyword in research_keywords):
                st.session_state.research_step = 2  # Go to clarification
            else:
                # For simple questions, you might want to implement a simpler Q&A agent
                # For now, we'll treat it as a new research topic
                st.session_state.research_step = 2
            
            st.rerun()
        
        if submit_research and new_question:
            # Start new research process
            st.session_state.query = new_question
            st.session_state.clarification = ""
            st.session_state.research_step = 2  # Go to clarification step
            save_message(st.session_state.current_session_id, "user", f"New research request: {new_question}")
            st.rerun()
    
    # Show session management options
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Current Session"):
        st.session_state.research_step = 1
        st.session_state.query = ""
        st.session_state.clarification = ""
        st.rerun()