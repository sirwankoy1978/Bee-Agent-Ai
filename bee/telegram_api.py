"""Direct Telegram Bot API client (public HTTP API, no wrapper libraries).

Implements the subset of https://core.telegram.org/bots/api that the project
needs beyond what the Agno webhook interface does for you:

- getMe            -> verify the token
- setWebhook       -> point Telegram at your public HTTPS URL + secret_token
- getWebhookInfo   -> inspect pending_error_count / last_error_message
- deleteWebhook    -> switch back to polling (getUpdates)
- setMyCommands    -> bot menu entries
- sendMessage      -> quick notifications (e.g. "webhook registered")
- getUpdates       -> discovery helper to read chat_id values

Uses httpx (already installed as an `openai` dependency). All calls are
synchronous so they are trivial to use from CLI scripts.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

API_BASE = "https://api.telegram.org"


class TelegramAPIError(RuntimeError):
    def __init__(self, method: str, payload: Dict[str, Any]):
        self.method = method
        self.payload = payload
        description = payload.get("description", "unknown error")
        super().__init__(f"Telegram API `{method}` failed (error_code="
                         f"{payload.get('error_code')}): {description}")


class TelegramBotAPI:
    """Thin, explicit client over the public Bot API HTTP endpoints."""

    def __init__(self, token: str, timeout: float = 30.0):
        if not token:
            raise ValueError("Bot token is required (from @BotFather).")
        self.token = token
        self.timeout = timeout

    # ------------------------------------------------------------------ core
    def _call(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{API_BASE}/bot{self.token}/{method}"
        response = httpx.post(url, json=payload or {}, timeout=self.timeout)
        body = response.json()
        if not body.get("ok"):
            raise TelegramAPIError(method, body)
        return body["result"]

    # ----------------------------------------------------------- bot methods
    def get_me(self) -> Dict[str, Any]:
        """core.telegram.org/bots/api#getme"""
        return self._call("getMe")

    def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None,
        max_connections: int = 40,
        allowed_updates: Optional[List[str]] = None,
    ) -> bool:
        """core.telegram.org/bots/api#setwebhook

        `allowed_updates` defaults to what the Agno Telegram interface handles:
        new messages and edits. `secret_token` is echoed back by Telegram in the
        `X-Telegram-Bot-Api-Secret-Token` header on every delivery.
        """
        payload: Dict[str, Any] = {
            "url": url,
            "max_connections": max_connections,
            "allowed_updates": allowed_updates or ["message", "edited_message"],
        }
        if secret_token:
            payload["secret_token"] = secret_token
        return bool(self._call("setWebhook", payload))

    def get_webhook_info(self) -> Dict[str, Any]:
        """core.telegram.org/bots/api#getwebhookinfo"""
        return self._call("getWebhookInfo")

    def delete_webhook(self, drop_pending_updates: bool = True) -> bool:
        """core.telegram.org/bots/api#deletewebhook"""
        return bool(self._call("deleteWebhook", {"drop_pending_updates": drop_pending_updates}))

    def set_my_commands(self, commands: List[Dict[str, str]]) -> bool:
        """core.telegram.org/bots/api#setmycommands"""
        return bool(self._call("setMyCommands", {"commands": commands}))

    def send_message(
        self,
        chat_id: str | int,
        text: str,
        reply_to_message_id: Optional[int] = None,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> Dict[str, Any]:
        """core.telegram.org/bots/api#sendmessage (Telegram's 4096-char limit applies)."""
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return self._call("sendMessage", payload)

    def get_updates(self, offset: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """core.telegram.org/bots/api#getupdates - only works while no webhook is set."""
        payload: Dict[str, Any] = {"limit": limit, "timeout": 0}
        if offset is not None:
            payload["offset"] = offset
        return self._call("getUpdates", payload)

    # ------------------------------------------------------------- utilities
    def describe(self) -> str:
        me = self.get_me()
        info = self.get_webhook_info()
        lines = [
            f"Bot: @{me['username']} ({me.get('first_name', '')})  id={me['id']}",
            f"Webhook URL: {info.get('url') or '<none - polling mode>'}",
            f"Has custom secret: {info.get('has_custom_secret', False)}",
            f"Pending updates: {info.get('pending_update_count', 0)}",
        ]
        if info.get("last_error_message"):
            lines.append(f"Last error: {info['last_error_message']}")
            lines.append(f"Retry at (unix): {info.get('last_error_timestamp')}")
        if info.get("allowed_updates"):
            lines.append(f"Allowed updates: {', '.join(info['allowed_updates'])}")
        return "\n".join(lines)


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
