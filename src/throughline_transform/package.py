# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""Containers (SR-0011): a zip, or the same files written into a folder.

Every timestamp is the same fixed value, so the same graph exported twice
produces identical bytes. An output that differs only in when it was taken
cannot be compared with the one before it, and comparing them is a thing
people do with a specification.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

Entry = tuple[str, bytes]

#: 1980-01-01 00:00:00 — the epoch of the zip format itself.
_EPOCH = (1980, 1, 1, 0, 0, 0)


def archive(entries: list[Entry]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, data in entries:
            info = zipfile.ZipInfo(path, date_time=_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Regular file, rw-r--r--, so the member unpacks with sane permissions.
            info.external_attr = 0o100644 << 16
            zf.writestr(info, data)
    return buffer.getvalue()


def unpack(entries: list[Entry], folder: Path) -> list[Path]:
    """Write the entries beneath ``folder``. Refuses a path that would escape it."""
    folder = folder.resolve()
    written: list[Path] = []
    for path, data in entries:
        target = (folder / path).resolve()
        if folder != target and folder not in target.parents:
            raise ValueError(f"refusing to write outside {folder}: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written.append(target)
    return written


_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def xml(text: str) -> str:
    """XML text escaping, needed by every part of both Office formats.

    A control character is not legal in XML 1.0 at all, and an item's text is
    arbitrary content from a repository — so they go rather than producing a
    file the reader refuses to open. Tab, newline and carriage return stay.
    """
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return _CONTROL.sub("", text)


def utf8(text: str) -> bytes:
    return text.encode("utf-8")
