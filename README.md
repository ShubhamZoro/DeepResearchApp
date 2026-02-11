# 🔍 Deep Research App

An AI-powered deep research assistant built with **Streamlit** and **OpenAI Agents**. Ask any question and get a comprehensive, well-structured research report — focused on the **latest confirmed findings** and recent developments.

## ✨ Features

- **Multi-Agent Research Pipeline** — A team of specialized AI agents work together:
  - 🧠 **Planner Agent** — Generates targeted search queries with recency focus
  - 🌐 **Search Agent** — Performs web searches and summarizes the latest findings
  - ✍️ **Writer Agent** — Synthesizes everything into a detailed markdown report
  - 💬 **Clarification Agent** — Asks follow-up questions to narrow your research scope

- **Recency-First Approach** — Prioritizes recent, confirmed research and developments over speculative future predictions

- **Session Management** — Create, switch between, and delete research sessions with full chat history

- **Interactive Follow-ups** — Continue the conversation with follow-up questions or start new research within the same session

## 🌐 Live Demo

👉 [**Try it here**](https://deepresearchapp-vhvo2j92b7vpk3ecj5uwpy.streamlit.app/)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- An OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/DeepResearchApp.git
   cd DeepResearchApp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   ```

4. **Run the app**
   ```bash
   streamlit run deep_research.py
   ```

## 🏗️ Architecture

```
User Query
    │
    ▼
┌──────────────┐
│ Clarify Agent │  ← Asks clarifying questions
└──────┬───────┘
       ▼
┌──────────────┐
│ Planner Agent │  ← Generates 10 targeted search queries (recency-focused)
└──────┬───────┘
       ▼
┌──────────────┐
│ Search Agent  │  ← Runs web searches in parallel, summarizes latest findings
└──────┬───────┘
       ▼
┌──────────────┐
│ Writer Agent  │  ← Produces a detailed markdown report (1000+ words)
└──────────────┘
```

## 📁 Project Structure

| File | Description |
|------|-------------|
| `deep_research.py` | Main Streamlit app with UI and session management |
| `research_manager.py` | Orchestrates the full research pipeline |
| `planner_agent.py` | Plans search queries with recency keywords |
| `search_agent.py` | Performs web searches and extracts latest findings |
| `writer_agent.py` | Writes the final comprehensive report |
| `clarify_agent.py` | Generates clarifying questions for the user |
| `email_agent.py` | (Optional) Sends the report via email |
| `chat_db.py` | SQLite-based chat history and session storage |

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **AI Framework**: [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- **LLM**: GPT-4o-mini
- **Database**: SQLite (via SQLAlchemy)
- **Web Search**: OpenAI WebSearchTool

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
