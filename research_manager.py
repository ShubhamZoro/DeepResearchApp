import asyncio
from datetime import datetime
from agents import Runner, trace, gen_trace_id
from email_agent import email_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from search_agent import search_agent

class ResearchManager:
    async def run(self, query: str, recipient_email: str = None):
        """Run the deep research process, yielding status updates and final report."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            #yield f"🔗 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            yield "🔍 Planning searches..."
            search_plan = await self.plan_searches(query)

            yield "🌐 Performing web searches..."
            search_results = await self.perform_searches(search_plan)

            yield "📝 Writing final report..."
            report = await self.write_report(query, search_results)

            if recipient_email:
                yield f"📧 Sending report to {recipient_email}..."
                await self.send_email(report, recipient_email)
                yield f"✅ Research complete. Report sent to {recipient_email}!"
            else:
                yield "✅ Research complete!"
            yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        current_date = datetime.now().strftime('%B %d, %Y')
        result = await Runner.run(
            planner_agent,
            f"Today's date is {current_date}. Focus on finding the LATEST information.\n\nQuery: {query}"
        )
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                if result:
                    results.append(result)
            except Exception:
                continue
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        input_text = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(search_agent, input_text)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        input_text = f"Original query: {query}\n\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input_text)
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData, recipient_email: str) -> None:
        await Runner.run(
            email_agent,
            f"Send this report to {recipient_email}.\n\nReport:\n{report.markdown_report}"
        )

    async def send_email_report(self, report_content: str, recipient_email: str) -> None:
        """Send a report via email given raw report content and recipient email."""
        await Runner.run(
            email_agent,
            f"Send this report to {recipient_email}.\n\nReport:\n{report_content}"
        )
