from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agents import Agent
from datetime import datetime

load_dotenv(override=True)


HOW_MANY_SEARCHES = 10

CURRENT_YEAR = datetime.now().year

INSTRUCTIONS = (
    f"You are a helpful research assistant. Given a query, come up with a set of web searches "
    f"to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for.\n\n"
    f"CRITICAL: Today's date is {datetime.now().strftime('%B %d, %Y')}. The current year is {CURRENT_YEAR}. "
    f"You MUST focus on finding the LATEST and most RECENT information. "
    f"Include the current year '{CURRENT_YEAR}' or 'latest' or 'recent' or '{CURRENT_YEAR - 1}-{CURRENT_YEAR}' "
    f"in your search queries to ensure results are up-to-date. "
    f"Avoid generic search terms that would return outdated results. "
    f"At least half of your search queries should include a year or recency keyword.\n\n"
    f"IMPORTANT: Focus search queries on CONFIRMED developments, published research, and things that have ALREADY HAPPENED. "
    f"Do NOT create queries about future predictions, upcoming events, or speculation. "
    f"Use terms like 'published', 'released', 'breakthroughs', 'study results', 'announced' rather than 'upcoming', 'future', 'predictions'."
)

# Use Pydantic to define the Schema of our response - this is known as "Structured Outputs"
# With massive thanks to student Wes C. for discovering and fixing a nasty bug with this!

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")

    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
