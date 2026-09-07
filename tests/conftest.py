# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""Fixture graphs, built by the tool itself.

Every graph a test reads is made with ``tl init``, ``tl new`` and ``tl link``
rather than written by hand, so the fixture cannot drift from the format the
installed tool reads and writes. Built once per session: the tests only read.

Two graphs: a plain one, and a consumer that adopts the plain one as a source by
path, so the composed path is exercised with no network.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(sys.executable).parent


def _tl(root: Path, *args: str, compose: bool = False) -> str:
    exe = BIN / ("tl-compose" if compose else "tl")
    if not exe.exists():  # pragma: no cover - only when the suite runs outside its venv
        exe = Path(shutil.which(exe.name) or exe.name)
    done = subprocess.run([str(exe), "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, f"{exe.name} {' '.join(args)}:\n{done.stdout}\n{done.stderr}"
    return done.stdout


def _init(root: Path, name: str) -> None:
    root.mkdir(parents=True)
    _tl(root, "init", "--name", name, "--no-defaults")
    config = root / "throughline.toml"
    text = config.read_text(encoding="utf-8")
    head = text[: text.index("[grounding]")]
    tail = text[text.index("[status]") :]
    if "# Coverage:" in tail:
        tail = tail[: tail.index("# Coverage:")]
    model = """[grounding]
root_types = ["intent", "non_goal"]
delivery_roots = ["intent"]
ground_link_types = ["derives_from", "implements"]
ai_origins = ["ai", "hybrid"]

[types.intent]
attrs.origin = { type = "enum", values = ["human", "ai", "hybrid"] }

[types.non_goal]
attrs.origin = { type = "enum", values = ["human", "ai", "hybrid"] }

[types.user_requirement]
attrs.origin = { type = "enum", values = ["human", "ai", "hybrid"] }

[types.system_requirement]
attrs.origin = { type = "enum", values = ["human", "ai", "hybrid"] }
attrs.priority = { type = "enum", values = ["must", "should", "could"], normative = true }
attrs.verification = { type = "string" }

[links]
types = ["derives_from", "implements", "refines", "relates", "satisfies"]

[link_rules]
derives_from = { from = ["user_requirement"], to = ["intent"] }
implements   = { from = ["system_requirement"], to = ["user_requirement"] }

"""
    config.write_text(head + model + tail, encoding="utf-8")
    for prefix, folder, title in (
        ("INT", "intents", "Intents"),
        ("NG", "non-goals", "Non-goals"),
        ("UR", "user-requirements", "User requirements"),
        ("SR", "system-requirements", "System requirements"),
    ):
        _tl(root, "register", "new", prefix, folder, "--title", title)


def _new(root: Path, prefix: str, type_: str, title: str, text: str, **kw: str) -> str:
    args = ["new", prefix, "--type", type_, "--origin", "human", "--title", title, "--text", text, "--no-interactive"]
    if "ground" in kw:
        args += ["--ground", kw["ground"], "--ground-type", kw["ground_type"]]
    for k, v in kw.items():
        if k.startswith("attr_"):
            args += ["--attr", f"{k[5:]}={v}"]
    out = _tl(root, *args)
    return out.split()[1]


@pytest.fixture(scope="session")
def plain_graph(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A small graph: an intent, a non-goal, two user requirements, three system requirements."""
    root = tmp_path_factory.mktemp("graphs") / "plain"
    _init(root, "Plain fixture")
    intent = _new(root, "INT", "intent", "Readers who will never open the editor", "A graph reaches people who read documents.")
    _new(root, "NG", "non_goal", "No second renderer", "Item prose is never rendered here.")
    ur1 = _new(root, "UR", "user_requirement", "Export as a document", "A reviewer gets a document: title, contents, items.", ground=intent, ground_type="derives_from")
    ur2 = _new(root, "UR", "user_requirement", "Export as a table", "A reviewer gets rows: one per item.", ground=intent, ground_type="derives_from")
    sr1 = _new(
        root, "SR", "system_requirement", "Markdown through the tool: a colon, \"quotes\" & <angles>",
        "The tool writes the Markdown.\nA second line of text.", ground=ur1, ground_type="implements",
        attr_priority="must", attr_verification="Compare with tl docs.",
    )
    sr2 = _new(root, "SR", "system_requirement", "Declare it in [[sources]]", "Prose mentioning [[sources]] the TOML table.", ground=ur2, ground_type="implements", attr_priority="should")
    sr3 = _new(root, "SR", "system_requirement", "Unlinked beyond grounding", "Nothing else.", ground=ur2, ground_type="implements", attr_priority="could")
    _tl(root, "link", sr2, sr1, "--type", "relates")
    _tl(root, "link", sr3, sr1, "--type", "refines")
    _tl(root, "amend", sr1, "--rationale", "Because a second renderer drifts. Rejected: writing it here.")
    _tl(root, "check", "--strict")
    return root


@pytest.fixture(scope="session")
def composed_graph(tmp_path_factory: pytest.TempPathFactory, plain_graph: Path) -> Path:
    """A consumer that adopts the plain graph by path and cites one of its clauses."""
    root = tmp_path_factory.mktemp("graphs") / "consumer"
    _init(root, "Composed fixture")
    config = root / "throughline.toml"
    text = config.read_text(encoding="utf-8")
    source = f'\n[[sources]]\nnamespace = "src"\npath = "{plain_graph.as_posix()}"\n\n'
    config.write_text(text.replace("[grounding]", source + "[grounding]", 1), encoding="utf-8")
    intent = _new(root, "INT", "intent", "Consume a source", "This graph borrows.")
    ur = _new(root, "UR", "user_requirement", "Cite a clause", "One requirement satisfies a borrowed clause.", ground=intent, ground_type="derives_from")
    sr = _new(root, "SR", "system_requirement", "Satisfies the source", "It does what the clause says.", ground=ur, ground_type="implements", attr_priority="must")
    _tl(root, "link", sr, "src:SR-0001", "--type", "satisfies", compose=True)
    _tl(root, "check", "--strict", compose=True)
    return root


@pytest.fixture(scope="session")
def git_graph(tmp_path_factory: pytest.TempPathFactory, plain_graph: Path) -> Path:
    """The plain graph copied into a git repository with one commit and then a dirty edit."""
    repo = tmp_path_factory.mktemp("repos") / "repo"
    shutil.copytree(plain_graph, repo / "idd")
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True)  # noqa: E731
    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "Test")
    git("remote", "add", "origin", "git@github.com:example/fixture.git")
    git("add", ".")
    git("commit", "-q", "-m", "fixture")
    return repo / "idd"
