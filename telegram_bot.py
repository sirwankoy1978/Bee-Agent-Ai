"""Bee-Agent-Ai - Telegram AI agent powered by Agno (AgentOS) + public OpenAI API.

Main entrypoint, following the official structure from
https://docs.agno.com/agent-os/interfaces/telegram (setup + introduction):

    python telegram_bot.py                # start AgentOS (webhook server)
    python telegram_bot.py set-webhook --url https://<tunnel>/telegram/webhook
    python telegram_bot.py webhook-info   # inspect webhook + last errors
    python telegram_bot.py delete-webhook # fall back to polling (getUpdates)
    python telegram_bot.py find-chat-id   # after deleting webhook: read chat ids
    python telegram_bot.py openai-check   # validate OpenAI key + model access
    python telegram_bot.py telegram-check # validate bot token via getMe

Environment variables (all optional, see bee/config.py and .env.example):
    OPENAI_API_KEY, TELEGRAM_TOKEN, TELEGRAM_WEBHOOK_SECRET_TOKEN, APP_ENV,
    OPENAI_MODEL, OPENAI_API_KIND, OPENAI_REASONING_EFFORT, BOT_MODE,
    TELEGRAM_STREAMING, TELEGRAM_SHOW_REASONING, TG_REPLY_TO_MENTIONS_ONLY,
    TG_REPLY_TO_BOT_MESSAGES, ENABLE_WEB_SEARCH, ENABLE_IMAGE_GENERATION,
    ENABLE_USER_MEMORY, TELEGRAM_CHAT_ID, PORT, HOST ...
"""

from __future__ import annotations

import argparse
import sys

from agno.os.app import AgentOS
from agno.os.interfaces.telegram import Telegram

from bee.agent import build_entity
from bee.config import get_settings


# --- User-facing messages -----------------------------------------------------
# The interface intercepts /start, /help and /new; everything else reaches the
# agent. Bilingual strings are data, not code, so the model talks to Arabic and
# English users alike.

START_MESSAGE = (
    "Hello! I'm Bee 🐝 - an AI agent running on Agno + the OpenAI API.\n"
    "مرحباً! أنا Bee 🐝 وكيل ذكاء اصطناعي يعمل عبر Agno وواجهة OpenAI.\n\n"
    "DM me: text, photos, voice notes, videos, documents or stickers.\n"
    "In groups: @mention me or reply to one of my messages - I stay silent otherwise.\n"
    "في المجموعات: اذكرني بـ @ أو ردّ على إحدى رسائلي، ولن أتكلم إلا عند ذلك.\n\n"
    "/help - what I can do | /new - reset this conversation"
)

HELP_MESSAGE = (
    "Here is what I can do:\n"
    "- Chat with live web search, reasoning scratchpad and long-term memory\n"
    "- Read photos / voice notes / video / documents you send me\n"
    "- Generate images with the OpenAI images API on request\n"
    "- /new resets the conversation, commands work in DMs and groups\n"
    "\n"
    "هذا ما أستطيع فعله: محادثة مع بحث ويب وأدوات تفكير وذاكرة، قراءة الصور "
    "والمقاطع الصوتية والمستندات، توليد صور عند الطلب. أرسل /new لبدء محادثة جديدة."
)

ERROR_MESSAGE = (
    "Sorry, something went wrong while processing your message. "
    "Send /new to start a fresh conversation.\n"
    "عذراً، حدث خطأ أثناء معالجة رسالتك. أرسل /new لبدء محادثة جديدة."
)

NEW_MESSAGE = (
    "New conversation started. How can I help you?\n"
    "بدأت محادثة جديدة. كيف أستطيع مساعدتك؟"
)

BOT_COMMANDS = [
    {"command": "start", "description": "Start the bot / ابدأ البوت"},
    {"command": "help", "description": "Show help / التعليمات"},
    {"command": "new", "description": "New conversation / محادثة جديدة"},
]


def build_agent_os(settings) -> tuple[AgentOS, object, str]:
    """Compose the AgentOS app exactly as the official Telegram docs prescribe:
    entity + interface -> AgentOS -> FastAPI app.
    """
    entity, kind = build_entity(settings)

    telegram_interface = Telegram(
        **{kind: entity},
        prefix=settings.tg_prefix,
        token=settings.telegram_token,
        # Token-by-token streaming with throttled live edits (docs: streaming).
        streaming=settings.tg_streaming,
        # Separate "Reasoning:" message before the answer (non-streaming only).
        show_reasoning=settings.tg_show_reasoning,
        # Group policy for this project: mentions + replies to the bot only.
        reply_to_mentions_only=settings.tg_reply_to_mentions_only,
        reply_to_bot_messages=settings.tg_reply_to_bot_messages,
        start_message=START_MESSAGE,
        help_message=HELP_MESSAGE,
        error_message=ERROR_MESSAGE,
        new_message=NEW_MESSAGE,
        commands=BOT_COMMANDS,
        register_commands=settings.tg_register_commands,
        quoted_responses=settings.tg_quoted_responses,
    )

    kwargs = {"tracing": settings.tracing}
    if settings.mcp:
        kwargs["mcp"] = True
    if kind == "team":
        agent_os = AgentOS(teams=[entity], interfaces=[telegram_interface], **kwargs)
    elif kind == "workflow":
        agent_os = AgentOS(workflows=[entity], interfaces=[telegram_interface], **kwargs)
    else:
        agent_os = AgentOS(agents=[entity], interfaces=[telegram_interface], **kwargs)
    return agent_os, entity, kind


def cmd_serve(settings) -> int:
    agent_os, entity, kind = build_agent_os(settings)
    app = agent_os.get_app()

    mode = "development (webhook secret check DISABLED)" if settings.is_dev else "production (webhook secret enforced)"
    print(f"[bee] mode={settings.bot_mode} entity={getattr(entity, 'id', kind)}")
    print(f"[bee] model={settings.openai_model} via {settings.openai_api_kind} API")
    print(f"[bee] webhook secret env APP_ENV -> {mode}")
    if not settings.is_dev:
        print("[bee] set the SAME TELEGRAM_WEBHOOK_SECRET_TOKEN when calling setWebhook.")
    print(f"[bee] status endpoint: http://{settings.host}:{settings.port}{settings.tg_prefix}/status")
    print(f"[bee] webhook endpoint: POST {settings.tg_prefix}/webhook")

    # Docs pattern: `agent_os.serve(app="telegram_bot:app", ...)` - uvicorn
    # auto-reload wants the import string, plain runs can pass `app`.
    try:
        agent_os.serve(
            app="telegram_bot:app" if settings.reload else app,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
        )
    except OSError as exc:  # e.g. address already in use
        print(f"[bee] could not start server: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_set_webhook(settings, url: str) -> int:
    from bee.telegram_api import TelegramBotAPI

    api = TelegramBotAPI(settings.telegram_token)
    if not url.startswith("https://"):
        print("[bee] warning: Telegram requires a public HTTPS webhook URL.", file=sys.stderr)
    ok = api.set_webhook(url=url, secret_token=settings.webhook_secret_token)
    api.set_my_commands(BOT_COMMANDS)
    print(f"[bee] setWebhook -> {ok}")
    print(api.describe())
    return 0


def cmd_delete_webhook(settings) -> int:
    from bee.telegram_api import TelegramBotAPI

    api = TelegramBotAPI(settings.telegram_token)
    print(f"[bee] deleteWebhook -> {api.delete_webhook(drop_pending_updates=True)}")
    print("[bee] the bot now drains updates via getUpdates (python telegram_bot.py find-chat-id)")
    return 0


def cmd_find_chat_id(settings) -> int:
    from bee.telegram_api import TelegramAPIError, TelegramBotAPI

    api = TelegramBotAPI(settings.telegram_token)
    try:
        updates = api.get_updates()
    except TelegramAPIError as exc:
        print(
            "[bee] getUpdates is unavailable while a webhook is set "
            "(Telegram API rule). Run `python telegram_bot.py delete-webhook` first, "
            "send the bot a message, then retry.\n",
            file=sys.stderr,
        )
        print(f"[bee] api said: {exc}", file=sys.stderr)
        return 1
    if not updates:
        print("[bee] no pending updates. Message the bot first, then re-run this command.")
        return 1
    seen: dict[str, str] = {}
    for update in updates:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat")
        if chat:
            seen[str(chat["id"])] = f"{chat.get('type')} - {chat.get('title') or chat.get('username') or chat.get('first_name')}"
    for chat_id, label in seen.items():
        print(f"chat_id={chat_id}  ({label})")
    print("\n[bee] export one of them as TELEGRAM_CHAT_ID to enable outbound TelegramTools.")
    print("[bee] remember to re-register the webhook (set-webhook) to resume real-time delivery.")
    return 0


def cmd_telegram_check(settings) -> int:
    from bee.telegram_api import TelegramAPIError, TelegramBotAPI

    try:
        print(TelegramBotAPI(settings.telegram_token).describe())
    except Exception as exc:
        print(f"[bee] telegram check failed: {exc}", file=sys.stderr)
        print("[bee] hint: verify TELEGRAM_TOKEN and network access to api.telegram.org.", file=sys.stderr)
        return 1
    return 0


def cmd_openai_check(settings) -> int:
    from bee.openai_api import check_model_available, ping

    try:
        report = check_model_available(settings)
        for key, value in report.items():
            print(f"{key}: {value}")
        print("[bee] pinging chat.completions ...")
        print("ping:", ping(settings))
    except Exception as exc:
        print(f"[bee] openai check failed: {exc}", file=sys.stderr)
        print("[bee] hint: verify OPENAI_API_KEY / OPENAI_MODEL in .env or bee/config.py.", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="telegram_bot.py", description="Bee Telegram agent (Agno + OpenAI + Telegram Bot API)")
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=["serve", "set-webhook", "delete-webhook", "webhook-info", "find-chat-id", "telegram-check", "openai-check"],
        help="what to run (default: serve)",
    )
    parser.add_argument("--url", help="public HTTPS webhook URL for set-webhook")
    args = parser.parse_args(argv)

    settings = get_settings()

    if args.command == "serve":
        return cmd_serve(settings)
    if args.command == "set-webhook":
        if not args.url:
            parser.error("set-webhook needs --url https://<host>/telegram/webhook")
        return cmd_set_webhook(settings, args.url)
    if args.command == "webhook-info":
        from bee.telegram_api import TelegramBotAPI

        print(TelegramBotAPI(settings.telegram_token).describe())
        return 0
    if args.command == "delete-webhook":
        return cmd_delete_webhook(settings)
    if args.command == "find-chat-id":
        return cmd_find_chat_id(settings)
    if args.command == "telegram-check":
        return cmd_telegram_check(settings)
    if args.command == "openai-check":
        return cmd_openai_check(settings)
    return 2


app = None  # Populated lazily below for `agent_os.serve(app="telegram_bot:app")`.

if __name__ == "__main__":
    sys.exit(main())
else:
    # When imported via the uvicorn reload string "telegram_bot:app", build the
    # FastAPI app at import time.
    _settings = get_settings()
    _agent_os, _entity, _kind = build_agent_os(_settings)
    app = _agent_os.get_app()
