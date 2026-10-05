"""Agent / Team / Workflow factories.

All entities are exposed to Telegram through the official Agno interface
(`agno.os.interfaces.telegram.Telegram`), but the reasoning itself runs on the
public OpenAI API (`openai` SDK underneath `agno.models.openai`), and outbound
Telegram actions use the public Telegram Bot API directly (`bee.telegram_api`).
"""

from __future__ import annotations



from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat, OpenAIResponses
from agno.team import Team
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.workflow import Workflow

from bee.config import Settings
from bee.prompts import (
    AGENT_INSTRUCTIONS,
    TEAM_INSTRUCTIONS,
    WORKFLOW_INSTRUCTIONS_DRAFT,
    WORKFLOW_INSTRUCTIONS_EDIT,
)

MEMORY_CAPTURE_INSTRUCTIONS = """\
Collect the user's name and preferred language.
Collect information about the user's interests, hobbies and projects.
Collect the user's likes and dislikes about how they want answers formatted.
Collect what the user is currently working on, so future chats can continue naturally.
"""


def build_model(settings: Settings):
    """Create the OpenAI model object used by every entity.

    Uses the public OpenAI API through the official `openai` SDK. `OPENAI_API_KIND`
    switches between the Chat Completions endpoint ("chat") and the newer
    Responses endpoint ("responses"); `OPENAI_REASONING_EFFORT` maps directly to
    the `reasoning_effort` parameter documented on platform.openai.com
    (minimal | low | medium | high for GPT-5 family models).
    """
    kwargs = {"api_key": settings.openai_api_key, "id": settings.openai_model}
    if settings.openai_reasoning_effort:
        kwargs["reasoning_effort"] = settings.openai_reasoning_effort
    if settings.openai_api_kind == "responses":
        return OpenAIResponses(**kwargs)
    return OpenAIChat(**kwargs)


def _build_db(settings: Settings) -> SqliteDb:
    """Persistent session storage - required for `/new` and cross-restart memory."""
    return SqliteDb(db_file=settings.db_file, session_table=settings.session_table)


def _build_tools(settings: Settings) -> list:
    """Agent tools, each one guarded by a config flag.

    - WebSearchTools (DuckDuckGo, no API key): live information.
    - ReasoningTools: chain-of-thought scratchpad for complex questions.
    - OpenAITools: direct public OpenAI API capabilities - GPT Image generation
      and Whisper transcription / TTS speech, sent back as native Telegram media.
    - TelegramTools: outbound actions against the public Telegram Bot API.
    """
    tools: list = []

    if settings.enable_web_search:
        try:
            from agno.tools.websearch import WebSearchTools  # requires `ddgs`

            tools.append(WebSearchTools())
        except ImportError:
            print("[bee] `ddgs` not installed - web search disabled "
                  "(fix: pip install ddgs).")

    if settings.enable_reasoning_tools:
        from agno.tools.reasoning import ReasoningTools

        tools.append(ReasoningTools(add_instructions=True))

    if settings.enable_image_generation or settings.enable_tts:
        from agno.tools.openai import OpenAITools

        tools.append(
            OpenAITools(
                api_key=settings.openai_api_key,
                enable_image_generation=settings.enable_image_generation,
                # Audio in Telegram chats: transcribe voice notes...
                enable_transcription=True,
                # ...and optionally speak replies (adds cost per message).
                enable_speech_generation=settings.enable_tts,
                image_model=settings.openai_image_model,
            )
        )

    if settings.use_telegram_tools:
        from agno.tools.telegram import TelegramTools

        tools.append(
            TelegramTools(
                token=settings.telegram_token,
                chat_id=settings.telegram_chat_id or None,
                all=True,  # send/edit/delete/react/pin/get_chat/get_file
            )
        )

    return tools


def build_agent(settings: Settings) -> Agent:
    """The single-agent mode (default). Mirrors docs: agent-os/usage/interfaces/telegram."""
    from agno.memory.manager import MemoryManager

    kwargs = dict(
        id="bee-telegram-agent",
        name="Bee Telegram Bot",
        model=build_model(settings),
        db=_build_db(settings),
        tools=_build_tools(settings),
        instructions=AGENT_INSTRUCTIONS,
        add_history_to_context=True,
        num_history_runs=settings.num_history_runs,
        add_datetime_to_context=True,
        markdown=True,
    )
    if settings.enable_user_memory:
        kwargs["memory_manager"] = MemoryManager(
            model=build_model(settings),
            memory_capture_instructions=MEMORY_CAPTURE_INSTRUCTIONS,
        )
        kwargs["enable_agentic_memory"] = True
    return Agent(**kwargs)


def build_team(settings: Settings) -> Team:
    """Multi-agent mode: a leader delegates to a Researcher and a Writer."""
    researcher = Agent(
        name="Researcher",
        model=build_model(settings),
        role="Researches topics and provides detailed factual information.",
        instructions=["Provide well-researched, factual information on the given topic."],
        tools=[t for t in _build_tools(settings) if type(t).__name__ in {"WebSearchTools", "ReasoningTools"}],
    )
    writer = Agent(
        name="Writer",
        model=build_model(settings),
        role="Takes research and writes clear, engaging summaries.",
        instructions=["Write concise, engaging summaries based on the research provided."],
    )
    return Team(
        id="bee-telegram-team",
        name="Bee Research Team",
        model=build_model(settings),
        members=[researcher, writer],
        db=_build_db(settings),
        instructions=TEAM_INSTRUCTIONS,
        add_history_to_context=True,
        num_history_runs=settings.num_history_runs,
        add_datetime_to_context=True,
        markdown=True,
    )


def build_workflow(settings: Settings) -> Workflow:
    """Draft -> Edit pipeline exposed as one Telegram bot."""
    drafter = Agent(
        name="Drafter",
        model=build_model(settings),
        instructions=WORKFLOW_INSTRUCTIONS_DRAFT,
    )
    editor = Agent(
        name="Editor",
        model=build_model(settings),
        instructions=WORKFLOW_INSTRUCTIONS_EDIT,
    )
    return Workflow(
        id="bee-telegram-workflow",
        name="Bee Draft-Edit Workflow",
        description="Two-step workflow that drafts and then edits replies for Telegram",
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
        db=_build_db(settings),
    )


def build_entity(settings: Settings):
    """Factory used by the entrypoint: returns (entity, kind)."""
    if settings.bot_mode == "team":
        return build_team(settings), "team"
    if settings.bot_mode == "workflow":
        return build_workflow(settings), "workflow"
    return build_agent(settings), "agent"
