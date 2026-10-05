"""09 - Multiple Telegram bots on one AgentOS server (docs: .../telegram/multiple-instances).

Telegram allows ONE webhook per bot token, so each interface needs its own bot.
Create a second bot via @BotFather, then:

    TELEGRAM_TOKEN_RESEARCH=<second-bot-token> python examples/09_multiple_instances.py

Register one webhook per prefix:
    .../basic/webhook        and        .../web-research/webhook
"""

import os

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.tools.websearch import WebSearchTools

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(db_file="tmp/persistent_memory.db")

basic_agent = Agent(
    name="Basic Agent",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    db=agent_db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

web_research_agent = Agent(
    name="Web Research Agent",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    db=agent_db,
    tools=[WebSearchTools()],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
)

# One token per interface (main token from TELEGRAM_TOKEN, second from TELEGRAM_TOKEN_RESEARCH).
research_token = os.getenv("TELEGRAM_TOKEN_RESEARCH", settings.telegram_token)

agent_os = AgentOS(
    agents=[basic_agent, web_research_agent],
    interfaces=[
        Telegram(agent=basic_agent, prefix="/basic", token=settings.telegram_token),
        Telegram(agent=web_research_agent, prefix="/web-research", token=research_token),
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
