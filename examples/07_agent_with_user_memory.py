"""07 - Agent with cross-session user memory (docs: .../telegram/agent-with-user-memory).

MemoryManager captures name/hobbies/preferences; enable_agentic_memory lets the
model itself store facts. Requires a database.
Run:  python examples/07_agent_with_user_memory.py
"""

from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory.manager import MemoryManager
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.tools.websearch import WebSearchTools

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(db_file="tmp/telegram_memory.db")

memory_manager = MemoryManager(
    memory_capture_instructions="""\
                    Collect User's name,
                    Collect Information about user's passion and hobbies,
                    Collect Information about the users likes and dislikes,
                    Collect information about what the user is doing with their life right now
                """,
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
)

personal_agent = Agent(
    name="Personal Friend Agent",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    tools=[WebSearchTools()],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
    db=agent_db,
    memory_manager=memory_manager,
    enable_agentic_memory=True,
    instructions=dedent("""
        You are a personal AI friend of the user, your purpose is to chat with the user and make them feel good.
        First introduce yourself and ask for their name then, ask about themselves, their hobbies,
        what they like to do and what they like to talk about.
        Use web search to find latest information about things in the conversations.
    """),
)

agent_os = AgentOS(
    agents=[personal_agent],
    interfaces=[Telegram(agent=personal_agent, token=settings.telegram_token)],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
