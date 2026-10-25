"""Crash-safe file writes: a reader sees either the old file or the new one, never half of it."""

import asyncio
import contextlib
import os
import stat
import tempfile
import time
from pathlib import Path

_REPLACE_ATTEMPTS = 5
# mkstemp creates 0600 files; data files keep their old mode, new ones get the usual 0644.
_NEW_FILE_MODE = 0o644


def write_bytes_atomic(path: Path | str, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        try:
            mode = stat.S_IMODE(target.stat().st_mode)
        except FileNotFoundError:
            mode = _NEW_FILE_MODE
        os.chmod(tmp_name, mode)
        _replace(tmp_name, target)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
        raise


def write_text_atomic(path: Path | str, text: str) -> None:
    write_bytes_atomic(path, text.encode("utf-8"))


async def write_text_atomic_async(path: Path | str, text: str) -> None:
    await asyncio.to_thread(write_text_atomic, path, text)


def _replace(source: str, target: Path) -> None:
    # Windows refuses to replace a file that another process holds open for a moment
    # (antivirus, a concurrent reader); Linux never raises here.
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(0.05 * (attempt + 1))
