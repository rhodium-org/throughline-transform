# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""What the editor needs of this package (INT-0002): structure as data,
provenance stated by the caller, and running where there are no processes."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from throughline_transform import project
from throughline_transform.cli import main
from throughline_transform.provenance import CLEAN, DIRTY, UNTRACKED, stated

# --- blocks (SR-0012) --------------------------------------------------------


def test_blocks_output_is_the_documents_structure(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "doc.json"
    assert main(["blocks", "-C", str(plain_graph), "-o", str(out), "--body", "both"]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert set(doc) == {"provenance", "provenance_lines", "blocks"}
    assert doc["provenance"]["repository"] == "plain" and doc["provenance"]["tree"] == UNTRACKED
    blocks = doc["blocks"]
    assert blocks[0] == {"text": "plain — requirements", "heading": 1}
    items = [b for b in blocks if "item" in b]
    assert len(items) == 7
    sr1 = next(b for b in items if b["item"]["uid"] == "SR-0001")
    assert sr1["heading"] == 4 and sr1["item"]["type"] == "system_requirement" and sr1["item"]["status"] == "draft"
    assert any(b.get("quote") for b in blocks) and any(b.get("small") for b in blocks)
    assert any(b.get("group") and b["text"] == "System requirements" for b in blocks)
    assert any("table" in b for b in blocks)  # --body both carries the table of items
    # Absent fields are omitted rather than written as false or null.
    assert all(v not in (False, None, "") or k == "text" for b in blocks for k, v in b.items())


def test_blocks_agree_with_the_docx(plain_graph: Path, tmp_path: Path):
    assert main(["blocks", "-C", str(plain_graph), "-o", str(tmp_path / "b.json")]) == 0
    assert main(["docx", "-C", str(plain_graph), "-o", str(tmp_path / "d.docx")]) == 0
    headings = [b["text"] for b in json.loads((tmp_path / "b.json").read_text())["blocks"] if b.get("heading")]
    with zipfile.ZipFile(tmp_path / "d.docx") as zf:
        document = zf.read("word/document.xml").decode("utf-8")
    for text in headings:
        assert text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;") in document


def test_composed_blocks_carry_the_appendix(composed_graph: Path, tmp_path: Path):
    out = tmp_path / "c.json"
    assert main(["blocks", "-C", str(composed_graph), "-o", str(out)]) == 0
    blocks = json.loads(out.read_text())["blocks"]
    appendix = next(b for b in blocks if b.get("group") and b["text"].startswith("Appendix A"))
    assert "subtitle" in appendix


# --- provenance stated by the caller (SR-0013) ------------------------------


def test_stated_provenance_replaces_git(git_graph: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []
    real = subprocess.run

    def spy(cmd, *a, **k):
        if cmd and cmd[0] == "git":
            calls.append(list(cmd))
        return real(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", spy)
    out = tmp_path / "s.md"
    assert main([
        "md", "-C", str(git_graph), "-o", str(out),
        "--repository", "x/y", "--ref", "v1", "--commit", "abc", "--tree", "clean",
    ]) == 0
    text = out.read_text()
    assert "- Repository: x/y" in text and "- Ref: v1" in text and "- Commit: abc" in text
    assert f"- Working tree: {CLEAN}" in text
    assert calls == []


def test_a_single_stated_flag_means_git_is_not_asked(git_graph: Path, tmp_path: Path):
    out = tmp_path / "r.md"
    assert main(["md", "-C", str(git_graph), "-o", str(out), "--repository", "only/this"]) == 0
    text = out.read_text()
    assert "- Repository: only/this" in text
    assert "- Ref: none" in text and "- Commit: none" in text
    assert f"- Working tree: {UNTRACKED}" in text


def test_tree_words():
    assert stated("t", "r", None, None, "dirty").tree == DIRTY
    assert stated("t", "r", None, None, "untracked").tree == UNTRACKED
    assert stated("t", None, None, None, None).repository == "graph"


# --- no processes (SR-0014) ---------------------------------------------------


def test_without_processes_the_entry_point_runs_in_process(plain_graph: Path, composed_graph: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    via_command = {}
    for fmt in ("md", "xlsx"):
        assert main([fmt, "-C", str(composed_graph), "-o", str(tmp_path / f"cmd.{fmt}"), "--repository", "r", "--tree", "clean"]) == 0
        via_command[fmt] = (tmp_path / f"cmd.{fmt}").read_bytes()

    monkeypatch.setattr(sys, "platform", "emscripten")
    assert not project.has_processes()

    def refuse(*a, **k):  # a process must never be started on this platform
        raise AssertionError("subprocess.run was called without processes")

    monkeypatch.setattr(subprocess, "run", refuse)
    for fmt in ("md", "xlsx"):
        assert main([fmt, "-C", str(composed_graph), "-o", str(tmp_path / f"in.{fmt}"), "--repository", "r", "--tree", "clean"]) == 0
        assert (tmp_path / f"in.{fmt}").read_bytes() == via_command[fmt]
    # The plain graph too: the core entry point, not only the composer's.
    assert main(["notes", "-C", str(plain_graph), "-o", str(tmp_path / "in-notes.zip"), "--repository", "r"]) == 0


def test_the_entry_point_is_resolved_from_metadata(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "emscripten")
    with pytest.raises(project.TransformError) as exc:
        project._in_process("no-such-command", ["--version"])
    assert "declares the no-such-command command" in str(exc.value)
    code, out, err = project._in_process("tl", ["--version"])
    assert code == 0 and out.startswith("tl ") and err == ""


def test_a_failing_tool_is_reported_in_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "emscripten")
    with pytest.raises(project.TransformError) as exc:
        project.run(tmp_path, ["dump"], composed=False)
    assert "tl dump failed" in str(exc.value)
