"""08 - Media agent: image generation + audio in/out (modern alternative to the
legacy DALL-E example; see docs note on .../telegram/agent-with-media).

Uses `OpenAITools(image_model="gpt-image-2")` as the docs recommend today, plus
Whisper transcription for voice notes. Generated media is delivered
automatically by the Telegram interface as native media messages.
Run:  python examples/08_agent_with_media.py
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram
from agno.tools.openai import OpenAITools

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from repo root: python examples/0X.py

from bee.config import get_settings

settings = get_settings()

agent_db = SqliteDb(session_table="telegram_media_sessions", db_file="tmp/telegram_media.db")

media_agent = Agent(
    name="Media Agent",
    model=OpenAIChat(api_key=settings.openai_api_key, id="gpt-5.4-mini"),
    db=agent_db,
    tools=[
        OpenAITools(
            api_key=settings.openai_api_key,
            enable_image_generation=True,
            image_model="gpt-image-2",
            enable_transcription=True,   # voice notes -> text via Whisper
            enable_speech_generation=True,  # text -> audio replies
        ),
    ],
    instructions=[
        "You are a helpful multimedia assistant on Telegram.",
        "When asked to generate, create, or draw an image, use the image generation tool.",
        "When asked to speak or read aloud, use the speech generation tool.",
        "You can also analyze images, audio, and video that users send you.",
        "Keep text responses concise and friendly.",
    ],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

agent_os = AgentOS(
    agents=[media_agent],
    interfaces=[
        Telegram(agent=media_agent, token=settings.telegram_token, reply_to_mentions_only=True)
    ],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app=app, host="0.0.0.0", port=7777, reload=False)
