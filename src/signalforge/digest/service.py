"""Daily link extraction and digest orchestration."""

from collections.abc import Sequence
from datetime import date

from signalforge.digest.models import (
    DigestContent,
    DigestMessage,
    DigestResult,
    MessageLink,
)
from signalforge.digest.ports import DigestGenerator, DigestRepository, MarkdownWriter
from signalforge.digest.timebox import utc_day_bounds
from signalforge.digest.urls import extract_urls

REQUIRED_HEADINGS = ("## Кратко", "## Основные темы", "## Полезные ссылки")
MAX_MESSAGES = 200
MAX_CHARACTERS = 60_000


class InvalidDigestError(ValueError):
    pass


class DailyDigestService:
    def __init__(
        self,
        repository: DigestRepository,
        generator: DigestGenerator,
        writer: MarkdownWriter,
    ) -> None:
        self._repository = repository
        self._generator = generator
        self._writer = writer

    def run(self, digest_date: date, timezone_name: str) -> DigestResult:
        start, end = utc_day_bounds(digest_date, timezone_name)
        all_messages = tuple(self._repository.messages_between(start, end))
        messages = _limit_messages(all_messages)
        links = _message_links(messages)
        self._repository.store_links(links)

        if messages:
            markdown = self._generator.generate(digest_date, messages, links).strip() + "\n"
            _validate_markdown(digest_date, markdown, links)
            model = self._generator.model
        else:
            markdown = _empty_digest(digest_date)
            model = "none"

        content = DigestContent(
            digest_date=digest_date,
            timezone=timezone_name,
            message_count=len(all_messages),
            link_count=len(links),
            markdown=markdown,
            model=model,
        )
        output_path = self._writer.write(digest_date, markdown)
        self._repository.save_digest(content)
        return DigestResult(content=content, output_path=output_path)


def _limit_messages(messages: Sequence[DigestMessage]) -> tuple[DigestMessage, ...]:
    selected: list[DigestMessage] = []
    characters = 0
    for message in messages[:MAX_MESSAGES]:
        remaining = MAX_CHARACTERS - characters
        if remaining <= 0:
            break
        text = message.text[:remaining]
        selected.append(
            DigestMessage(
                id=message.id,
                source_message_id=message.source_message_id,
                sent_at=message.sent_at,
                text=text,
            )
        )
        characters += len(text)
    return tuple(selected)


def _message_links(messages: Sequence[DigestMessage]) -> tuple[MessageLink, ...]:
    return tuple(
        MessageLink(message.id, message.source_message_id, url)
        for message in messages
        for url in extract_urls(message.text)
    )


def _validate_markdown(digest_date: date, markdown: str, links: Sequence[MessageLink]) -> None:
    if not markdown.startswith(f"# SignalForge — {digest_date.isoformat()}"):
        raise InvalidDigestError("digest title is missing")
    if any(heading not in markdown for heading in REQUIRED_HEADINGS):
        raise InvalidDigestError("required digest section is missing")
    source_ids = {link.source_message_id for link in links}
    if any(str(source_id) not in markdown for source_id in source_ids):
        raise InvalidDigestError("link source message ID is missing")


def _empty_digest(digest_date: date) -> str:
    return (
        f"# SignalForge — {digest_date.isoformat()}\n\n"
        "## Кратко\n\nЗа этот день сообщений нет.\n\n"  # noqa: RUF001
        "## Основные темы\n\nНет данных.\n\n"  # noqa: RUF001
        "## Полезные ссылки\n\nНет ссылок.\n"  # noqa: RUF001
    )
