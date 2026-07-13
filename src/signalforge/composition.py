"""Production composition root for SignalForge commands."""

from datetime import date
from typing import cast

from sqlalchemy import create_engine
from telethon.sync import TelegramClient

from signalforge.application.import_service import HistoryImportService
from signalforge.application.models import ImportSummary
from signalforge.digest.generator import ResponsesDigestGenerator, UrllibJsonTransport
from signalforge.digest.models import DigestResult
from signalforge.digest.service import DailyDigestService
from signalforge.digest.writer import AtomicMarkdownWriter
from signalforge.infrastructure.postgres.repositories import (
    SqlAlchemyDigestRepository,
    SqlAlchemyImportRunRepository,
    SqlAlchemyMessageRepository,
)
from signalforge.infrastructure.telegram.history_source import (
    SyncTelethonClient,
    TelethonHistorySource,
)
from signalforge.settings import DigestSettings, Settings


def execute_history_import(settings: Settings) -> ImportSummary:
    """Construct production adapters and execute one history import."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    client = TelegramClient(
        settings.telegram_session_path,
        settings.telegram_api_id,
        settings.telegram_api_hash,
        receive_updates=False,
    )
    source = TelethonHistorySource(cast(SyncTelethonClient, client), settings.telegram_chat)
    service = HistoryImportService(
        source,
        SqlAlchemyMessageRepository(engine),
        SqlAlchemyImportRunRepository(engine),
    )
    try:
        return service.run(str(settings.telegram_chat))
    finally:
        engine.dispose()


def execute_daily_digest(settings: DigestSettings, digest_date: date) -> DigestResult:
    """Construct production adapters and generate one daily digest."""
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    generator = ResponsesDigestGenerator(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        transport=UrllibJsonTransport(),
    )
    service = DailyDigestService(
        SqlAlchemyDigestRepository(engine),
        generator,
        AtomicMarkdownWriter(settings.output_dir),
    )
    try:
        return service.run(digest_date, settings.timezone)
    finally:
        engine.dispose()
