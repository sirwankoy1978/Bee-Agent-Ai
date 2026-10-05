"""06 - Reasoning agent: ReasoningTools + web search (docs: .../telegram/reasoning-agent).

Chain-of-thought scratchpad for complex questions, live data from web search.
Run:  python examples/06_reasoning_agent.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.tools.reasoning import ReasoningTools
from agno.tools.websearch import WebSearchTools

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(db_file="tmp/telegram_reasoning.db")

reasoning_agent = Agent(
    name="Reasoning Research Agent",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    db=agent_db,
    tools=[
        ReasoningTools(add_instructions=True),
        WebSearchTools(),
    ],
    instructions="Use tables to display data. When you use thinking tools, keep the thinking brief.",
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    agents=[reasoning_agent],
    interfaces=[Telegram(agent=reasoning_agent, token=settings.telegram_token)],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
