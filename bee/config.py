"""Central configuration for the Bee Telegram agent.

Reads settings from environment variables, with an optional `.env` file in the
project root. Defaults are safe for a first local run; every value can be
overridden without touching any other file.

NOTE ON SECRETS: the demo keys below are baked in so the project runs with zero
edits. Before making this repository public, remove them and rotate both keys
in the OpenAI dashboard and via @BotFather (`/revoke`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TMP_DIR = PROJECT_ROOT / "tmp"

# --- Built-in demo configuration (override with env vars or `.env`) ---------
DEFAULT_OPENAI_API_KEY = (
    "sk-proj-PV4TCPEyOPC8m_CtNq_EbUqH7A9o7tzodDFvrpycuPsYuapQu1wuTFNa9PYs"
    "lk8IgYRt3edOw4T3BlbkFJFlT82usXVxO9JAX0125Sx1AlMaqcOlEni9PshLcXiaT_j_"
    "DbyiNj2i5ftZjGhQ67rbvHM8vDMA"
)
DEFAULT_TELEGRAM_TOKEN = "8832479896:AAEm6kXTRRoQWNBRTeAG0QE6cbYHstGxPoA"
# Telegram accepts 1-256 letters, digits, underscores or hyphens (setWebhook).
DEFAULT_WEBHOOK_SECRET = "BeeAgent-DevWebhookSecret-01a10cc2"


def _load_dotenv(path: Path) -> None:
    """Tiny dependency-free `.env` loader (KEY=VALUE lines, `#` comments)."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def _env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default) or default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw not in (None, "") else default
    except ValueError:
        return default


@dataclass
class Settings:
    """Everything the bot needs, resolved once at import time."""

    # --- Credentials ---------------------------------------------------------
    openai_api_key: str = field(default_factory=lambda: _env_str("OPENAI_API_KEY", DEFAULT_OPENAI_API_KEY))
    telegram_token: str = field(default_factory=lambda: _env_str("TELEGRAM_TOKEN", DEFAULT_TELEGRAM_TOKEN))
    webhook_secret_token: str = field(default_factory=lambda: _env_str("TELEGRAM_WEBHOOK_SECRET_TOKEN", DEFAULT_WEBHOOK_SECRET))
    # "development" disables the webhook-secret check (Agno security module).
    app_env: str = field(default_factory=lambda: _env_str("APP_ENV", ""))

    # --- OpenAI model selection (public OpenAI API) --------------------------
    # "chat"     -> OpenAIChat      (Chat Completions API, v1/chat/completions)
    # "responses"-> OpenAIResponses (Responses API, v1/responses)
    openai_api_kind: str = field(default_factory=lambda: _env_str("OPENAI_API_KIND", "chat").lower())
    openai_model: str = field(default_factory=lambda: _env_str("OPENAI_MODEL", "gpt-5.4-mini"))
    openai_reasoning_effort: str = field(default_factory=lambda: _env_str("OPENAI_REASONING_EFFORT", ""))

    # --- Server --------------------------------------------------------------
    host: str = field(default_factory=lambda: _env_str("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("PORT", 7777))
    reload: bool = field(default_factory=lambda: _env_bool("RELOAD", False))

    # --- Bot mode (AgentOS entities supported by the Telegram interface) ----
    # "agent" | "team" | "workflow"
    bot_mode: str = field(default_factory=lambda: _env_str("BOT_MODE", "agent").lower())

    # --- Telegram interface parameters (docs: agent-os/interfaces/telegram) --
    tg_prefix: str = field(default_factory=lambda: _env_str("TG_PREFIX", "/telegram"))
    tg_streaming: bool = field(default_factory=lambda: _env_bool("TELEGRAM_STREAMING", True))
    tg_show_reasoning: bool = field(default_factory=lambda: _env_bool("TELEGRAM_SHOW_REASONING", False))
    # Group policy requested for this project:
    # answer ONLY when @mentioned or when replying to the bot's own message.
    tg_reply_to_mentions_only: bool = field(default_factory=lambda: _env_bool("TG_REPLY_TO_MENTIONS_ONLY", True))
    tg_reply_to_bot_messages: bool = field(default_factory=lambda: _env_bool("TG_REPLY_TO_BOT_MESSAGES", True))
    tg_quoted_responses: bool = field(default_factory=lambda: _env_bool("TG_QUOTED_RESPONSES", False))
    tg_register_commands: bool = field(default_factory=lambda: _env_bool("TG_REGISTER_COMMANDS", True))

    # --- Agent capabilities ---------------------------------------------------
    num_history_runs: int = field(default_factory=lambda: _env_int("NUM_HISTORY_RUNS", 3))
    enable_web_search: bool = field(default_factory=lambda: _env_bool("ENABLE_WEB_SEARCH", True))
    enable_reasoning_tools: bool = field(default_factory=lambda: _env_bool("ENABLE_REASONING_TOOLS", True))
    enable_image_generation: bool = field(default_factory=lambda: _env_bool("ENABLE_IMAGE_GENERATION", True))
    openai_image_model: str = field(default_factory=lambda: _env_str("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    enable_tts: bool = field(default_factory=lambda: _env_bool("ENABLE_TTS", False))
    enable_user_memory: bool = field(default_factory=lambda: _env_bool("ENABLE_USER_MEMORY", True))
    # Outbound "proactive" Telegram tools. Auto-enabled when TELEGRAM_CHAT_ID is set.
    telegram_chat_id: str = field(default_factory=lambda: _env_str("TELEGRAM_CHAT_ID", ""))
    enable_telegram_tools: bool = field(default_factory=lambda: _env_bool("ENABLE_TELEGRAM_TOOLS", False))

    # --- Storage ---------------------------------------------------------------
    db_file: str = field(default_factory=lambda: _env_str("DB_FILE", str(TMP_DIR / "bee_telegram.db")))
    session_table: str = field(default_factory=lambda: _env_str("SESSION_TABLE", "telegram_sessions"))

    # --- AgentOS extras ---------------------------------------------------------
    tracing: bool = field(default_factory=lambda: _env_bool("AGENTOS_TRACING", False))
    mcp: bool = field(default_factory=lambda: _env_bool("AGENTOS_MCP", False))

    # ------------------------------ helpers ---------------------------------
    @property
    def use_telegram_tools(self) -> bool:
        return self.enable_telegram_tools or bool(self.telegram_chat_id)

    @property
    def is_dev(self) -> bool:
        return self.app_env.strip().lower() == "development"

    def validate(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        if not self.telegram_token:
            raise RuntimeError("TELEGRAM_TOKEN is not set (get one from @BotFather).")
        if not self.is_dev and not self.webhook_secret_token:
            raise RuntimeError(
                "TELEGRAM_WEBHOOK_SECRET_TOKEN is required outside APP_ENV=development."
            )
        if self.bot_mode not in {"agent", "team", "workflow"}:
            raise RuntimeError(f"BOT_MODE must be agent|team|workflow, got {self.bot_mode!r}.")
        if self.openai_api_kind not in {"chat", "responses"}:
            raise RuntimeError(f"OPENAI_API_KIND must be chat|responses, got {self.openai_api_kind!r}.")
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        Path(self.db_file).parent.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    _load_dotenv(PROJECT_ROOT / ".env")
    settings = Settings()
    settings.validate()
    return settings
