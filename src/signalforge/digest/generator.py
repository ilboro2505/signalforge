"""Responses-compatible LLM adapter for daily digest generation."""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from signalforge.digest.models import DigestMessage, MessageLink


class DigestGenerationError(Exception):
    """Provider failure reduced to a secret-safe public code."""

    def __init__(self) -> None:
        super().__init__("llm_error")


class JsonTransport(Protocol):
    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout: float,
    ) -> object: ...


class UrllibJsonTransport:
    """Small JSON transport using only the Python standard library."""

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout: float,
    ) -> object:
        request = Request(
            url,
            data=json.dumps(payload).encode(),
            headers=dict(headers),
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            raise DigestGenerationError from None


@dataclass(frozen=True, slots=True)
class ResponsesDigestGenerator:
    api_key: str = field(repr=False)
    model: str
    base_url: str
    transport: JsonTransport
    timeout: float = 60.0

    def generate(
        self,
        digest_date: date,
        messages: Sequence[DigestMessage],
        links: Sequence[MessageLink],
    ) -> str:
        payload: dict[str, object] = {
            "model": self.model,
            "instructions": _instructions(digest_date),
            "input": _input(messages, links),
        }
        try:
            response = self.transport.post(
                f"{self.base_url.rstrip('/')}/responses",
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                payload,
                self.timeout,
            )
            return _output_text(response)
        except DigestGenerationError:
            raise
        except Exception:
            raise DigestGenerationError from None


def _instructions(digest_date: date) -> str:
    return (
        "Создай краткий Markdown-дайджест на русском языке только по входным данным. "
        "Не выдумывай факты или ссылки. Верни ровно заголовок "  # noqa: RUF001
        f"'# SignalForge — {digest_date.isoformat()}' и секции '## Кратко', "
        "'## Основные темы', '## Полезные ссылки'. Для каждой полезной ссылки "
        "укажи исходный Telegram message ID."
    )


def _input(messages: Sequence[DigestMessage], links: Sequence[MessageLink]) -> str:
    message_lines = [
        f"[{message.sent_at.isoformat()}] message_id={message.source_message_id}: {message.text}"
        for message in messages
    ]
    link_lines = [f"message_id={link.source_message_id}: {link.url}" for link in links]
    return "MESSAGES\n" + "\n".join(message_lines) + "\n\nLINKS\n" + "\n".join(link_lines)


def _output_text(response: object) -> str:
    if not isinstance(response, dict):
        raise DigestGenerationError
    top_level = response.get("output_text")
    if isinstance(top_level, str) and top_level.strip():
        return top_level

    chunks: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict) or not isinstance(item.get("content"), list):
                continue
            for content in cast(list[object], item["content"]):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if content.get("type") in {"output_text", "text"} and isinstance(text, str):
                    chunks.append(text)
    result = "\n".join(chunks).strip()
    if not result:
        raise DigestGenerationError
    return result
