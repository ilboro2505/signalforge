"""Technology-independent daily digest models."""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DigestMessage:
    id: int
    source_message_id: int
    sent_at: datetime
    text: str


@dataclass(frozen=True, slots=True)
class MessageLink:
    message_id: int
    source_message_id: int
    url: str


@dataclass(frozen=True, slots=True)
class DigestContent:
    digest_date: date
    timezone: str
    message_count: int
    link_count: int
    markdown: str
    model: str


@dataclass(frozen=True, slots=True)
class DigestResult:
    content: DigestContent
    output_path: Path
