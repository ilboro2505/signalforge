"""SignalForge command-line entry point."""

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    """Build the root parser without registering product commands yet."""
    return argparse.ArgumentParser(
        prog="signalforge",
        description="SignalForge knowledge pipeline",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Display the root help until an approved task adds product commands."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
