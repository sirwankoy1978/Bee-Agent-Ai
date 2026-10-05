"""05 - Streaming Workflow with live step progress (docs: .../telegram/streaming-workflow).

Users see which step is running in real time ("research..." -> "research").
Run:  python examples/05_streaming_workflow.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.tools.websearch import WebSearchTools
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.workflow import Workflow

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

db = SqliteDb(
    session_table="telegram_streaming_wf_sessions",
    db_file="tmp/telegram_streaming_workflow.db",
)

researcher = Agent(
    name="Researcher",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    tools=[WebSearchTools()],
    instructions=[
        "Research the topic using web search.",
        "Provide bullet-point findings with sources.",
    ],
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    instructions=[
        "Write a clear, concise summary from the research.",
        "Use **bold** for key terms and keep it under 300 words.",
        "Suitable for reading on a phone screen.",
    ],
)

research_write_workflow = Workflow(
    name="Research and Write",
    description="Two-step workflow: research a topic, then write a polished summary",
    steps=[
        Steps(
            name="research_and_write",
            description="Research then write",
            steps=[
                Step(name="research", agent=researcher, description="Research the topic"),
                Step(name="write", agent=writer, description="Write the summary"),
            ],
        )
    ],
    db=db,
)

agent_os = AgentOS(
    workflows=[research_write_workflow],
    interfaces=[
        Telegram(
            workflow=research_write_workflow,
            token=settings.telegram_token,
            reply_to_mentions_only=True,
            streaming=True,
            start_message="Research bot ready. Send me a topic and I will research and summarize it.",
        )
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
