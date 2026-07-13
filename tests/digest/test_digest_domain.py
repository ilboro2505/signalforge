"""Unit tests for daily digest domain behavior."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from signalforge.digest.models import DigestContent, DigestMessage, MessageLink
from signalforge.digest.service import DailyDigestService, InvalidDigestError
from signalforge.digest.timebox import previous_local_day, utc_day_bounds
from signalforge.digest.urls import extract_urls
from signalforge.digest.writer import AtomicMarkdownWriter


def test_day_boundaries_and_previous_day_for_moscow() -> None:
    start, end = utc_day_bounds(date(2026, 7, 12), "Europe/Moscow")
    assert start == datetime(2026, 7, 11, 21, tzinfo=UTC)
    assert end == datetime(2026, 7, 12, 21, tzinfo=UTC)
    assert previous_local_day(datetime(2026, 7, 13, 1, tzinfo=UTC), "Europe/Moscow") == date(
        2026, 7, 12
    )


def test_extracts_normalizes_and_deduplicates_urls() -> None:
    text = (
        "See HTTPS://Example.COM/path?q=1#part, again "
        "https://example.com/path?q=1#other and ftp://example.com/no. "
        "Wrapped (https://example.org/docs)."
    )
    assert extract_urls(text) == (
        "https://example.com/path?q=1",
        "https://example.org/docs",
    )


@dataclass
class FakeRepository:
    messages: list[DigestMessage]
    links: list[MessageLink] = field(default_factory=list)
    digests: list[DigestContent] = field(default_factory=list)
    bounds: tuple[datetime, datetime] | None = None

    def messages_between(self, start: datetime, end: datetime) -> list[DigestMessage]:
        self.bounds = (start, end)
        return self.messages

    def store_links(self, links: Sequence[MessageLink]) -> None:
        self.links.extend(links)

    def save_digest(self, content: DigestContent) -> None:
        self.digests[:] = [content]


@dataclass
class FakeGenerator:
    calls: int = 0
    seen_messages: tuple[DigestMessage, ...] = ()
    seen_links: tuple[MessageLink, ...] = ()
    model: str = "fake-model"

    def generate(
        self,
        digest_date: date,
        messages: Sequence[DigestMessage],
        links: Sequence[MessageLink],
    ) -> str:
        self.calls += 1
        self.seen_messages = tuple(messages)
        self.seen_links = tuple(links)
        return (
            f"# SignalForge — {digest_date}\n\n## Кратко\n\nИтог.\n\n"  # noqa: RUF001
            "## Основные темы\n\n- Тема\n\n## Полезные ссылки\n\n"
            f"- {links[0].url} — message {links[0].source_message_id}"
        )


def test_service_extracts_links_generates_and_atomically_replaces(tmp_path: Path) -> None:
    repository = FakeRepository(
        [
            DigestMessage(
                id=10,
                source_message_id=77,
                sent_at=datetime(2026, 7, 12, 10, tzinfo=UTC),
                text="Useful https://example.com/tool#readme",
            )
        ]
    )
    generator = FakeGenerator()
    service = DailyDigestService(repository, generator, AtomicMarkdownWriter(tmp_path))

    first = service.run(date(2026, 7, 12), "Europe/Moscow")
    second = service.run(date(2026, 7, 12), "Europe/Moscow")

    assert generator.calls == 2
    assert generator.seen_links[0].url == "https://example.com/tool"
    assert generator.seen_links[0].source_message_id == 77
    assert first.output_path == second.output_path == tmp_path / "2026-07-12.md"
    assert first.output_path.read_text() == second.content.markdown
    assert repository.digests == [second.content]


def test_empty_day_skips_generator_and_writes_deterministic_digest(tmp_path: Path) -> None:
    repository = FakeRepository([])
    generator = FakeGenerator()

    result = DailyDigestService(repository, generator, AtomicMarkdownWriter(tmp_path)).run(
        date(2026, 7, 12), "Europe/Moscow"
    )

    assert generator.calls == 0
    assert result.content.model == "none"
    assert result.content.message_count == 0
    assert "За этот день сообщений нет" in result.content.markdown  # noqa: RUF001
    assert result.output_path.exists()


def test_rejects_generated_digest_without_link_source_id(tmp_path: Path) -> None:
    repository = FakeRepository(
        [
            DigestMessage(
                id=10,
                source_message_id=77,
                sent_at=datetime(2026, 7, 12, 10, tzinfo=UTC),
                text="Useful https://example.com/tool",
            )
        ]
    )

    class MissingSourceGenerator(FakeGenerator):
        def generate(
            self,
            digest_date: date,
            messages: Sequence[DigestMessage],
            links: Sequence[MessageLink],
        ) -> str:
            return (
                f"# SignalForge — {digest_date}\n\n## Кратко\n\nSafe.\n\n"
                "## Основные темы\n\n- Topic\n\n## Полезные ссылки\n\n- URL"
            )

    with pytest.raises(InvalidDigestError):
        DailyDigestService(
            repository, MissingSourceGenerator(), AtomicMarkdownWriter(tmp_path)
        ).run(date(2026, 7, 12), "Europe/Moscow")

    assert not (tmp_path / "2026-07-12.md").exists()
