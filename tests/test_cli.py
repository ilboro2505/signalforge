"""Tests for safe import-history CLI behavior."""

import json
from uuid import uuid4

import pytest
from _pytest.capture import CaptureFixture

from signalforge.application.errors import FatalImportError, ImportErrorCode
from signalforge.application.models import ImportCounts, ImportStatus, ImportSummary
from signalforge.cli import main
from signalforge.settings import Settings


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
