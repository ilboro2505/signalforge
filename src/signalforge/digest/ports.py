"""Ports used by the daily digest pipeline."""

from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from signalforge.digest.models import DigestContent, DigestMessage, MessageLink


class DigestRepository(Protocol):
    def messages_between(self, start: datetime, end: datetime) -> Sequence[DigestMessage]: ...

    def store_links(self, links: Sequence[MessageLink]) -> None: ...

    def save_digest(self, content: DigestContent) -> None: ...


class DigestGenerator(Protocol):
    @property
    def model(self) -> str: ...

    def generate(
        self,
        digest_date: date,
        messages: Sequence[DigestMessage],
        links: Sequence[MessageLink],
    ) -> str: ...


class MarkdownWriter(Protocol):
    def write(self, digest_date: date, markdown: str) -> Path: ...
