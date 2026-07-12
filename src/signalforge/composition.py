"""Production composition root for SignalForge commands."""

from typing import cast

from sqlalchemy import create_engine
from telethon.sync import TelegramClient

from signalforge.application.import_service import HistoryImportService
from signalforge.application.models import ImportSummary
from signalforge.infrastructure.postgres.repositories import (
    SqlAlchemyImportRunRepository,
    SqlAlchemyMessageRepository,
)
from signalforge.infrastructure.telegram.history_source import (
    SyncTelethonClient,
    TelethonHistorySource,
)
from signalforge.settings import Settings


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
