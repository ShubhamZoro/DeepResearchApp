import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from agents import Agent, function_tool
from typing import Dict

load_dotenv(override=True)

@function_tool
def send_email(subject: str, html_body: str, recipient_email: str) -> Dict[str, str]:
    """Send out an email with the given subject and HTML body to the specified recipient using Gmail SMTP"""
    sender_email = os.environ.get('GMAIL_EMAIL')
    sender_password = os.environ.get('GMAIL_APP_PASSWORD')

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add body to email
        msg.attach(MIMEText(html_body, 'html'))

        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        return {"status": "success", "message": f"Email sent to {recipient_email}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)