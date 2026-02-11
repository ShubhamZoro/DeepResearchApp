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
import os

# Setup
nest_asyncio.apply()
load_dotenv(override=True)
st.set_page_config(page_title="Deep Research", layout="wide")
# os.environ["OPENAI_API_KEY"] = st.secrets['OPENAI_API_KEY']
# os.environ["SENDGRID_API_KEY"] = st.secrets['SENDGRID_API_KEY']
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
if "processing_question" not in st.session_state:
    st.session_state.processing_question = False
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "sending_email" not in st.session_state:
    st.session_state.sending_email = False
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False

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
        # Step 3: Run full pipeline - but maintain chat history
        current_session_name = get_session_name(st.session_state.current_session_id)
        st.title(f"🔍 {current_session_name}")
        
        # Always show existing chat history first
        chat_history = get_chat_history(st.session_state.current_session_id)
        
        if chat_history:
            st.subheader("Previous Conversation")
            for role, content, timestamp in chat_history:
                if role == "user":
                    with st.chat_message("user"):
                        st.write(content)
                else:
                    with st.chat_message("assistant"):
                        st.write(content)
            
            st.divider()
        
        # Show current research processing
        st.subheader("🔍 Current Research in Progress")
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            
            full_query = f"{st.session_state.query}\n\nUser clarification:\n{st.session_state.clarification}"
            
            async def run_research():
                output = ""
                async for chunk in manager.run(full_query):
                    output += chunk + "\n\n"
                    placeholder.markdown(f"⚡ **Research Progress:**\n\n{output}")
                
                # Save the final output
                save_message(st.session_state.current_session_id, "assistant", output)
                st.session_state.research_step = 4  # Move to chat mode
                st.rerun()
            
            # Run the research
            asyncio.run(run_research())
    
    elif st.session_state.research_step == 4:
        # Chat mode - show all messages and allow new questions
        st.subheader("Research Conversation")
        
        # Always display chat history first
        chat_history = get_chat_history(st.session_state.current_session_id)
        
        # Create a container for chat history that stays visible
        chat_container = st.container()
        
        with chat_container:
            for role, content, timestamp in chat_history:
                if role == "user":
                    with st.chat_message("user"):
                        st.write(content)
                else:
                    with st.chat_message("assistant"):
                        st.write(content)
        
        # Check if we're currently processing a question
        if "processing_question" in st.session_state and st.session_state.processing_question:
            # Show processing status while maintaining chat history
            with st.chat_message("assistant"):
                processing_placeholder = st.empty()
                
                # Process the question
                async def process_question():
                    question = st.session_state.current_question
                    output = ""
                    
                    # Check if this looks like a new research request
                    research_keywords = ["research", "analyze", "study", "investigate", "explore", "find information about"]
                    
                    if any(keyword in question.lower() for keyword in research_keywords):
                        # Full research pipeline
                        processing_placeholder.markdown("🔍 **Planning searches...**")
                        
                        async for chunk in manager.run(question):
                            output += chunk + "\n\n"
                            processing_placeholder.markdown(f"⚡ **Processing Research...**\n\n{output}")
                    else:
                        # Simple follow-up - you can customize this logic
                        processing_placeholder.markdown("🤔 **Thinking...**")
                        await asyncio.sleep(1)  # Simulate processing
                        output = f"Thank you for your follow-up question: '{question}'\n\nThis appears to be a follow-up question. For comprehensive research on this topic, please use the 'New Research' button or include research keywords in your question."
                        processing_placeholder.markdown(output)
                    
                    # Save the response
                    save_message(st.session_state.current_session_id, "assistant", output)
                    
                    # Clear processing state
                    st.session_state.processing_question = False
                    st.session_state.current_question = ""
                    
                    # Rerun to show updated chat
                    st.rerun()
                
                # Run the processing
                asyncio.run(process_question())
        
        # Input section at the bottom
        st.divider()
        st.subheader("💬 Continue Conversation")
        
        # Create a form for the chat input
        with st.form("chat_form", clear_on_submit=True):
            new_question = st.text_area(
                "Ask a follow-up question or start new research:",
                placeholder="Ask a follow-up question, request clarification, or start a new research topic...",
                height=100,
                key="new_question_input"
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                submit_chat = st.form_submit_button("💬 Send Message", use_container_width=True)
            
            with col2:
                submit_research = st.form_submit_button("🔍 New Research", use_container_width=True, type="secondary")
        
        # Handle form submissions
        if submit_chat and new_question:
            # Save user message immediately
            save_message(st.session_state.current_session_id, "user", new_question)
            
            # Set processing state
            st.session_state.processing_question = True
            st.session_state.current_question = new_question
            
            # Rerun to show the user message and start processing
            st.rerun()
        
        if submit_research and new_question:
            # Save user message
            save_message(st.session_state.current_session_id, "user", f"🔍 New research request: {new_question}")
            
            # Start new research process
            st.session_state.query = new_question
            st.session_state.clarification = ""
            st.session_state.research_step = 2  # Go to clarification step
            st.rerun()
        
        # Email Report Section
        st.divider()
        st.subheader("📧 Email Report")
        
        if st.session_state.email_sent:
            st.success("✅ Report sent successfully!")
            if st.button("Send to another email"):
                st.session_state.email_sent = False
                st.session_state.sending_email = False
                st.rerun()
        elif st.session_state.sending_email:
            with st.form("email_form", clear_on_submit=False):
                email_address = st.text_input(
                    "Enter recipient email:",
                    placeholder="your-email@example.com"
                )
                send_btn = st.form_submit_button("📤 Send Report", use_container_width=True)
            
            if send_btn and email_address:
                # Get the latest assistant message (the report)
                report_content = ""
                for role, content, timestamp in reversed(chat_history):
                    if role == "assistant":
                        report_content = content
                        break
                
                if report_content:
                    with st.spinner("📧 Sending report..."):
                        async def send_report_email():
                            await manager.send_email_report(report_content, email_address.strip())
                        asyncio.run(send_report_email())
                    st.session_state.email_sent = True
                    st.session_state.sending_email = False
                    st.rerun()
                else:
                    st.error("No report found to send.")
            
            if st.button("Cancel"):
                st.session_state.sending_email = False
                st.rerun()
        else:
            if st.button("📧 Send Report via Email", use_container_width=True):
                st.session_state.sending_email = True
                st.session_state.email_sent = False
                st.rerun()
    
    # Show session management options
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset Current Session"):
        st.session_state.research_step = 1
        st.session_state.query = ""
        st.session_state.clarification = ""
        st.rerun()

