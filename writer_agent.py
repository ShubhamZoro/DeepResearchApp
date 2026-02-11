from pydantic import BaseModel, Field
from dotenv import load_dotenv
from datetime import datetime
from agents import Agent

CURRENT_DATE = datetime.now().strftime('%B %d, %Y')
CURRENT_YEAR = datetime.now().year

INSTRUCTIONS = (
    f"You are a senior researcher tasked with writing a cohesive report for a research query. "
    f"Today's date is {CURRENT_DATE}. "
    f"You will be provided with the original query, and some initial research done by a research assistant.\n"
    f"You should first come up with an outline for the report that describes the structure and "
    f"flow of the report. Then, generate the report and return that as your final output.\n\n"
    f"CRITICAL RECENCY REQUIREMENTS:\n"
    f"- PRIORITIZE the most recent findings and developments (from {CURRENT_YEAR - 1}-{CURRENT_YEAR}).\n"
    f"- Always include specific dates, months, or timeframes when citing information.\n"
    f"- Lead each section with the latest developments FIRST, then provide historical context if needed.\n"
    f"- If any research data appears outdated, explicitly note it (e.g., 'Note: this data is from 2023 and may be outdated').\n"
    f"- Include a 'Latest Developments' or 'Recent Updates' section near the top of the report.\n"
    f"- Focus the report on CONFIRMED findings, published research, completed studies, and official announcements.\n"
    f"- Do NOT give significant space to speculative future predictions or upcoming unconfirmed events.\n"
    f"- If mentioning future events, keep it brief and clearly label them as unconfirmed/speculative.\n\n"
    f"IMPORTANT: Do NOT include any source URLs, links, references, citations, bibliography, "
    f"or 'Sources' / 'References' sections. Do NOT add footnotes or inline citation markers. "
    f"Present all information directly without attributing it to specific websites or articles.\n\n"
    f"The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    f"for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)