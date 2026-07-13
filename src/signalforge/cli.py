"""SignalForge command-line entry point."""

import argparse
import json
import os
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime

from signalforge.application.errors import FatalImportError
from signalforge.application.models import ImportStatus, ImportSummary
from signalforge.composition import execute_daily_digest, execute_history_import
from signalforge.digest.generator import DigestGenerationError
from signalforge.digest.models import DigestResult
from signalforge.digest.timebox import previous_local_day
from signalforge.settings import (
    ConfigurationError,
    DigestSettings,
    Settings,
    load_digest_settings,
    load_settings,
)

ImportRunner = Callable[[Settings], ImportSummary]
DigestRunner = Callable[[DigestSettings, date], DigestResult]


def build_parser() -> argparse.ArgumentParser:
    """Build the root parser and approved product commands."""
    parser = argparse.ArgumentParser(
        prog="signalforge",
        description="SignalForge knowledge pipeline",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "import-history",
        help="Import configured Telegram chat history into PostgreSQL",
    )
    digest_parser = subparsers.add_parser(
        "generate-digest",
        help="Generate a Markdown digest for one local day",
    )
    digest_parser.add_argument("--date", help="Local date in YYYY-MM-DD; defaults to yesterday")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    runner: ImportRunner = execute_history_import,
    digest_runner: DigestRunner = execute_daily_digest,
    now: Callable[[], datetime] | None = None,
) -> int:
    """Run one command and emit a machine-readable safe result."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help()
        return 0

    if arguments.command == "import-history":
        return _run_import(environ if environ is not None else os.environ, runner)
    if arguments.command == "generate-digest":
        return _run_digest(
            environ if environ is not None else os.environ,
            arguments.date,
            digest_runner,
            now or (lambda: datetime.now(UTC)),
        )

    parser.error("unknown command")
    return 1


def _run_import(environ: Mapping[str, str], runner: ImportRunner) -> int:
    try:
        summary = runner(load_settings(environ))
    except ConfigurationError:
        _print_failure("configuration_error")
        return 1
    except FatalImportError as error:
        _print_failure(error.code.value)
        return 1
    except Exception:
        _print_failure("internal_error")
        return 1

    print(json.dumps(_summary_payload(summary), sort_keys=True))
    if summary.status is ImportStatus.SUCCESS:
        return 0
    if summary.status is ImportStatus.PARTIAL:
        return 2
    return 1


def _summary_payload(summary: ImportSummary) -> dict[str, object]:
    return {
        "run_id": str(summary.run_id),
        "source_chat_ref": summary.source_chat_ref,
        "status": summary.status.value,
        "processed_count": summary.counts.processed,
        "new_count": summary.counts.new,
        "existing_count": summary.counts.existing,
        "skipped_count": summary.counts.skipped,
        "error_count": summary.counts.errors,
        "error_code": summary.error_code,
    }


def _run_digest(
    environ: Mapping[str, str],
    date_argument: str | None,
    runner: DigestRunner,
    now: Callable[[], datetime],
) -> int:
    try:
        settings = load_digest_settings(environ)
        digest_date = (
            date.fromisoformat(date_argument)
            if date_argument is not None
            else previous_local_day(now(), settings.timezone)
        )
        result = runner(settings, digest_date)
    except ValueError:
        _print_digest_failure("invalid_date")
        return 1
    except ConfigurationError:
        _print_digest_failure("configuration_error")
        return 1
    except DigestGenerationError:
        _print_digest_failure("llm_error")
        return 1
    except Exception:
        _print_digest_failure("internal_error")
        return 1

    print(
        json.dumps(
            {
                "status": "success",
                "date": result.content.digest_date.isoformat(),
                "message_count": result.content.message_count,
                "link_count": result.content.link_count,
                "path": str(result.output_path),
            },
            sort_keys=True,
        )
    )
    return 0


def _print_failure(error_code: str) -> None:
    print(
        json.dumps(
            {
                "status": "failed",
                "processed_count": 0,
                "new_count": 0,
                "existing_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "error_code": error_code,
            },
            sort_keys=True,
        )
    )


def _print_digest_failure(error_code: str) -> None:
    print(json.dumps({"status": "failed", "error_code": error_code}, sort_keys=True))
