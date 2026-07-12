"""Smoke tests for the project skeleton."""

from _pytest.capture import CaptureFixture

from signalforge import __version__
from signalforge.cli import main


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_stub_prints_help(capsys: CaptureFixture[str]) -> None:
    exit_code = main([])

    assert exit_code == 0
    # Avoid coupling the skeleton test to argparse formatting details.
    output = capsys.readouterr().out
    assert "SignalForge knowledge pipeline" in output
    assert "import-history" in output
