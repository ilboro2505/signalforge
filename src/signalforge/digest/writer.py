"""Atomic filesystem writer for daily Markdown digests."""

import os
import tempfile
from datetime import date
from pathlib import Path


class AtomicMarkdownWriter:
    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def write(self, digest_date: date, markdown: str) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        target = self._output_dir / f"{digest_date.isoformat()}.md"
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=self._output_dir,
            prefix=f".{digest_date.isoformat()}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as stream:
                stream.write(markdown)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return target
