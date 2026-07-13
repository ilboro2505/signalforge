"""Tests for safe SignalForge CLI behavior."""

import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from _pytest.capture import CaptureFixture

from signalforge.application.errors import FatalImportError, ImportErrorCode
from signalforge.application.models import ImportCounts, ImportStatus, ImportSummary
from signalforge.cli import main
from signalforge.digest.generator import DigestGenerationError
from signalforge.digest.models import DigestContent, DigestResult
from signalforge.settings import DigestSettings, Settings


def valid_environment() -> dict[str, str]:
    return {
        "SIGNALFORGE_TELEGRAM_API_ID": "12345",
        "SIGNALFORGE_TELEGRAM_API_HASH": "api-secret-canary",
        "SIGNALFORGE_TELEGRAM_SESSION_PATH": "/tmp/session-secret-canary",
        "SIGNALFORGE_TELEGRAM_CHAT": "-100123",
        "SIGNALFORGE_DATABASE_URL": "postgresql+psycopg://secret-canary@localhost/db",
    }


def summary(status: ImportStatus) -> ImportSummary:
    return ImportSummary(
        run_id=uuid4(),
        source_chat_ref="safe-chat",
        status=status,
        counts=ImportCounts(processed=3, new=1, existing=1, skipped=1),
    )


@pytest.mark.parametrize(
    ("status", "expected_exit"),
    [
        (ImportStatus.SUCCESS, 0),
        (ImportStatus.PARTIAL, 2),
        (ImportStatus.FAILED, 1),
    ],
)
def test_emits_json_summary_and_documented_exit_codes(
    status: ImportStatus,
    expected_exit: int,
    capsys: CaptureFixture[str],
) -> None:
    def runner(_settings: Settings) -> ImportSummary:
        return summary(status)

    exit_code = main(
        ["import-history"],
        environ=valid_environment(),
        runner=runner,
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == expected_exit
    assert payload["status"] == status.value
    assert payload["processed_count"] == 3
    assert payload["new_count"] == 1


def test_configuration_failure_does_not_leak_secret_canaries(
    capsys: CaptureFixture[str],
) -> None:
    environment = valid_environment()
    environment.pop("SIGNALFORGE_TELEGRAM_CHAT")

    exit_code = main(["import-history"], environ=environment)

    output = capsys.readouterr().out
    assert exit_code == 1
    assert json.loads(output)["error_code"] == "configuration_error"
    assert "secret-canary" not in output


def test_fatal_adapter_failure_is_reduced_to_safe_code(capsys: CaptureFixture[str]) -> None:
    def failing_runner(_settings: Settings) -> ImportSummary:
        raise FatalImportError(ImportErrorCode.TELEGRAM_AUTH)

    exit_code = main(
        ["import-history"],
        environ=valid_environment(),
        runner=failing_runner,
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert json.loads(output)["error_code"] == "telegram_auth_error"
    assert "secret-canary" not in output


def test_unexpected_failure_is_redacted(capsys: CaptureFixture[str]) -> None:
    def failing_runner(_settings: Settings) -> ImportSummary:
        raise RuntimeError("secret-canary from dependency")

    exit_code = main(
        ["import-history"],
        environ=valid_environment(),
        runner=failing_runner,
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert json.loads(output)["error_code"] == "internal_error"
    assert "secret-canary" not in output


def digest_environment() -> dict[str, str]:
    return {
        "SIGNALFORGE_DATABASE_URL": "postgresql://db-secret-canary@localhost/db",
        "SIGNALFORGE_LLM_API_KEY": "llm-secret-canary",
        "SIGNALFORGE_LLM_MODEL": "model",
        "SIGNALFORGE_DIGEST_OUTPUT_DIR": "/tmp/digests",
    }


def test_generate_digest_defaults_to_previous_local_day_and_emits_json(
    capsys: CaptureFixture[str],
) -> None:
    def digest_runner(settings: DigestSettings, digest_date: date) -> DigestResult:
        assert settings.timezone == "Europe/Moscow"
        assert digest_date == date(2026, 7, 12)
        return DigestResult(
            DigestContent(digest_date, settings.timezone, 3, 2, "safe", settings.llm_model),
            Path("/tmp/digests/2026-07-12.md"),
        )

    exit_code = main(
        ["generate-digest"],
        environ=digest_environment(),
        digest_runner=digest_runner,
        now=lambda: datetime(2026, 7, 13, 1, tzinfo=UTC),
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == {
        "date": "2026-07-12",
        "link_count": 2,
        "message_count": 3,
        "path": "/tmp/digests/2026-07-12.md",
        "status": "success",
    }


def test_generate_digest_accepts_explicit_date(capsys: CaptureFixture[str]) -> None:
    seen: list[date] = []

    def digest_runner(settings: DigestSettings, digest_date: date) -> DigestResult:
        seen.append(digest_date)
        return DigestResult(
            DigestContent(digest_date, settings.timezone, 0, 0, "safe", "none"),
            Path("safe.md"),
        )

    assert (
        main(
            ["generate-digest", "--date", "2026-07-10"],
            environ=digest_environment(),
            digest_runner=digest_runner,
        )
        == 0
    )
    assert seen == [date(2026, 7, 10)]
    capsys.readouterr()


@pytest.mark.parametrize(
    ("date_argument", "expected_code"),
    [("not-a-date", "invalid_date"), (None, "llm_error")],
)
def test_generate_digest_failures_are_safe(
    date_argument: str | None,
    expected_code: str,
    capsys: CaptureFixture[str],
) -> None:
    def failing_runner(_settings: DigestSettings, _digest_date: date) -> DigestResult:
        raise DigestGenerationError

    argv = ["generate-digest"]
    if date_argument is not None:
        argv.extend(["--date", date_argument])
    exit_code = main(
        argv,
        environ=digest_environment(),
        digest_runner=failing_runner,
        now=lambda: datetime(2026, 7, 13, tzinfo=UTC),
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert json.loads(output)["error_code"] == expected_code
    assert "secret-canary" not in output
