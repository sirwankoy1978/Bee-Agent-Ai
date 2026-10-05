"""04 - Draft + Edit Workflow on Telegram (docs: agent-os/usage/interfaces/telegram/workflow).

The Workflow (not individual agents) is exposed; `Steps` chains `Step` objects.
Run:  python examples/04_workflow.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.workflow import Workflow

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(session_table="telegram_workflow_sessions", db_file="tmp/telegram_workflow.db")

drafter = Agent(
    name="Drafter",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    instructions="Draft a response to the user's message. Be helpful and informative.",
)

editor = Agent(
    name="Editor",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    instructions=[
        "Review and polish the draft for clarity and conciseness.",
        "Keep it short and suitable for a Telegram message.",
    ],
)

telegram_workflow = Workflow(
    name="Telegram Draft-Edit Workflow",
    description="A two-step workflow that drafts and then edits responses for Telegram",
    steps=[
        Steps(
            name="draft_and_edit",
            description="Draft then edit a response",
            steps=[
                Step(name="draft", agent=drafter, description="Draft an initial response"),
                Step(name="edit", agent=editor, description="Edit and polish the draft"),
            ],
        )
    ],
    db=agent_db,
)

agent_os = AgentOS(
    workflows=[telegram_workflow],
    interfaces=[
        Telegram(workflow=telegram_workflow, token=settings.telegram_token, reply_to_mentions_only=True)
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
