# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""Reaching the tool (SR-0001, SR-0002).

Two commands are asked of it and nothing else: ``dump`` for the structure and
``docs`` for the prose. Which entry point answers is decided by the graph, not
the caller — a graph that declares sources is composed, and the core command
run over it would exit cleanly and drop every borrowed clause's own reference
number, which is exactly the identifier a conformance document exists to carry.

The tool is reached as a command, not imported. Its command line is the surface
it publishes; its modules move between releases.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from .model import Graph, index

CONFIG = "throughline.toml"


class TransformError(Exception):
    """A failure the user can act on, reported in one line on stderr."""


def find_graph(start: str | os.PathLike[str] | None) -> Path:
    """The directory holding ``throughline.toml``.

    With ``-C``, that directory must be a graph — a wrong path is refused rather
    than searched around, because an export of the wrong graph reads exactly
    like the right one. Without it, the walk upward from the working directory
    is the one ``tl`` itself makes.
    """
    if start is not None:
        root = Path(start).resolve()
        if not (root / CONFIG).is_file():
            raise TransformError(f"{root} holds no {CONFIG}")
        return root
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG).is_file():
            return candidate
    raise TransformError(f"no {CONFIG} here or above; pass -C <dir>")


def is_composed(root: Path) -> bool:
    """Whether the graph declares sources, and so is the composer's to read."""
    with open(root / CONFIG, "rb") as fh:
        config = tomllib.load(fh)
    return bool(config.get("sources"))


def executable(name: str) -> str:
    """Where the tool is.

    Beside this interpreter first, because that is the tool this package was
    installed with and the one its floors were proven against; then the path.
    """
    beside = Path(sys.executable).parent / name
    if beside.is_file() and os.access(beside, os.X_OK):
        return str(beside)
    found = shutil.which(name)
    if found:
        return found
    raise TransformError(f"{name} is not installed beside this tool nor on the path")


def run(root: Path, args: list[str], composed: bool) -> str:
    """Run the tool over the graph and hand back what it wrote."""
    command = [executable("tl-compose" if composed else "tl"), "-C", str(root), *args]
    try:
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:  # pragma: no cover - the executable check above covers the common case
        raise TransformError(f"could not run {command[0]}: {exc}") from exc
    if done.returncode != 0:
        detail = done.stderr.strip() or done.stdout.strip() or f"exit {done.returncode}"
        raise TransformError(f"{Path(command[0]).name} {args[0]} failed — {detail}")
    return done.stdout


def load(root: Path) -> Graph:
    """The graph, as the tool exports it."""
    composed = is_composed(root)
    raw: dict[str, Any] = json.loads(run(root, ["dump"], composed))
    return index(raw, composed)


def docs(root: Path, document: str, composed: bool) -> str:
    """Hand the tool a document of directives and read back what it wrote.

    Written outside the graph, so an export can never be mistaken for a change
    to it and never reaches a commit.
    """
    with tempfile.TemporaryDirectory(prefix="tl-transform-") as scratch:
        path = Path(scratch) / "document.md"
        path.write_text(document, encoding="utf-8")
        run(root, ["docs", str(path)], composed)
        return path.read_text(encoding="utf-8")
