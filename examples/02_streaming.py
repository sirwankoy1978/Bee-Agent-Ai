"""02 - Streaming Telegram agent (docs: agent-os/usage/interfaces/telegram/streaming).

Token-by-token streaming: the bot posts a placeholder message, then edits it in
place (throttled to ~1 edit/s and honoring Telegram 429 `retry_after`).
Run:  python examples/02_streaming.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(session_table="telegram_sessions", db_file="tmp/telegram_streaming.db")

telegram_agent = Agent(
    name="Telegram Streaming Bot",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    db=agent_db,
    instructions=[
        "You are a helpful assistant on Telegram.",
        "Keep responses concise and friendly.",
        "In groups, respond when mentioned with @ or when someone replies to your message.",
    ],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    agents=[telegram_agent],
    interfaces=[
        Telegram(
            agent=telegram_agent,
            token=settings.telegram_token,
            reply_to_mentions_only=True,
            streaming=True,
        )
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)

