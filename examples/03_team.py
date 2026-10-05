"""03 - Multi-agent Team on Telegram (docs: agent-os/usage/interfaces/telegram/team).

A team leader delegates between a Researcher (with tools) and a Writer.
Run:  python examples/03_team.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.team import Team

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(session_table="telegram_team_sessions", db_file="tmp/telegram_team.db")

researcher = Agent(
    name="Researcher",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    role="Researches topics and provides detailed factual information.",
    instructions=["Provide well-researched, factual information on the given topic."],
)

writer = Agent(
    name="Writer",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    role="Takes research and writes clear, engaging summaries.",
    instructions=["Write concise, engaging summaries based on the research provided."],
)

telegram_team = Team(
    name="Telegram Research Team",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    members=[researcher, writer],
    db=agent_db,
    instructions=[
        "You coordinate a research team on Telegram.",
        "Use the Researcher to gather facts, then the Writer to create a response.",
        "Keep responses concise for Telegram.",
    ],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    teams=[telegram_team],
    interfaces=[
        Telegram(team=telegram_team, token=settings.telegram_token, reply_to_mentions_only=True)
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    # App object is passed directly so the example runs from any CWD
    # (`python examples/03_team.py` from the project root).
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
