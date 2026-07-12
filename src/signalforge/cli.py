"""SignalForge command-line entry point."""

import argparse
import json
import os
from collections.abc import Callable, Mapping, Sequence

from signalforge.application.errors import FatalImportError
from signalforge.application.models import ImportStatus, ImportSummary
from signalforge.composition import execute_history_import
from signalforge.settings import ConfigurationError, Settings, load_settings

ImportRunner = Callable[[Settings], ImportSummary]


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
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    runner: ImportRunner = execute_history_import,
) -> int:
    """Run one command and emit a machine-readable safe result."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command is None:
        parser.print_help()
        return 0

    if arguments.command == "import-history":
        return _run_import(environ if environ is not None else os.environ, runner)

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
