# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""Reaching the tool (SR-0001, SR-0002).

Two commands are asked of it and nothing else: ``dump`` for the structure and
``docs`` for the prose. Which entry point answers is decided by the graph, not
the caller — a graph that declares sources is composed, and the core command
run over it would exit cleanly and drop every borrowed clause's own reference
number, which is exactly the identifier a conformance document exists to carry.

The tool is reached as a command, not imported. Its command line is the surface
it publishes; its modules move between releases. Where the platform has no
processes — Python under Pyodide in a browser — the console entry point the
package declares in its own metadata is called in-process instead (SR-0014):
that entry point is what the ``tl`` command itself runs, so it is the command
by another route, not an import of the tool's modules for their functions.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from contextlib import redirect_stderr, redirect_stdout
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from .model import Graph, index
from .progress import slow

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


def has_processes() -> bool:
    """Whether this platform can start a process at all."""
    return sys.platform != "emscripten"


def _in_process(name: str, argv: list[str]) -> tuple[int, str, str]:
    """Call the console entry point the package declares for ``name``.

    Resolved from package metadata, never from a module path written here, so
    what runs is exactly what the ``tl`` command on a terminal runs.
    """
    found = [ep for ep in entry_points(group="console_scripts") if ep.name == name]
    if not found:
        raise TransformError(f"no package installed here declares the {name} command")
    main = found[0].load()
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return int(code or 0), out.getvalue(), err.getvalue()


def run(root: Path, args: list[str], composed: bool) -> str:
    """Run the tool over the graph and hand back what it wrote."""
    name = "tl-compose" if composed else "tl"
    argv = ["-C", str(root), *args]
    if has_processes():
        command = [executable(name), *argv]
        try:
            done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            code, stdout, stderr = done.returncode, done.stdout, done.stderr
        except OSError:
            # A platform that has an executable but cannot start it: the
            # entry point is the same command by the other route.
            code, stdout, stderr = _in_process(name, argv)
    else:
        code, stdout, stderr = _in_process(name, argv)
    if code != 0:
        detail = stderr.strip() or stdout.strip() or f"exit {code}"
        raise TransformError(f"{name} {args[0]} failed — {detail}")
    return stdout


def _tool(composed: bool) -> str:
    return "tl-compose" if composed else "tl"


def load(root: Path) -> Graph:
    """The graph, as the tool exports it."""
    composed = is_composed(root)
    fetching = " — its sources may be being fetched" if composed else ""
    with slow(f"still reading the graph with {_tool(composed)}{fetching}…"):
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
        with slow(f"still asking {_tool(composed)} to write the document…"):
            run(root, ["docs", str(path)], composed)
        return path.read_text(encoding="utf-8")
