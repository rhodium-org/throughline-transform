# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The assistant form (UR-0008, SR-0017, SR-0018): one file per register, each
carrying the register's items exactly as ``tl dump`` gives them, and a manifest
that says what the folder was true of and how to answer."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from throughline_transform.assistant import FORM_VERSION, INSTRUCTION, to_assistant
from throughline_transform.cli import main
from throughline_transform.project import change_set_format, load, run
from throughline_transform.provenance import CLEAN, Provenance, provenance_of

PROV = Provenance(repository="example/fixture", ref="main", commit="0" * 40, tree=CLEAN, tool="tl 2.2.0")
FENCE = re.compile(r"^```json\n(.*?)^```\n", re.S | re.M)


def _dump(root: Path) -> dict:
    return json.loads(run(root, ["dump"], False))


def _folder(root: Path, out: Path, *extra: str) -> dict[str, str]:
    assert main(["assistant", "-C", str(root), "-o", str(out), *extra]) == 0
    assert out.is_dir() and not out.with_suffix(".zip").exists()
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(out.iterdir())}


def _block(text: str) -> dict:
    blocks = FENCE.findall(text)
    assert len(blocks) == 1, "one fenced JSON block per file"
    return json.loads(blocks[0])


# --- SR-0017: one file per register, the dump's items unreshaped ----------------


def test_the_folder_holds_one_file_per_register_and_the_manifest(plain_graph: Path, tmp_path: Path):
    files = _folder(plain_graph, tmp_path / "form")
    dump = _dump(plain_graph)
    prefixes = [r["prefix"] for r in dump["registers"]]
    assert sorted(files) == sorted([f"{p}.json" for p in prefixes] + ["manifest.json"])
    seen = []
    for prefix in prefixes:
        data = json.loads(files[f"{prefix}.json"])
        assert data["register"]["prefix"] == prefix
        for item in data["items"]:
            assert item["uid"].startswith(prefix + "-")
            seen.append(item)
    # every item, and every link on it, appears exactly once and unchanged
    assert sorted(seen, key=lambda i: i["uid"]) == dump["items"]
    assert all("fingerprint" in item for item in seen)


def test_md_wrapping_holds_the_same_content_in_one_fenced_block(plain_graph: Path, tmp_path: Path):
    as_json = _folder(plain_graph, tmp_path / "json")
    as_md = _folder(plain_graph, tmp_path / "md", "--wrap", "md")
    assert sorted(as_md) == sorted(n.replace(".json", ".md") for n in as_json)
    for name, text in as_json.items():
        assert _block(as_md[name.replace(".json", ".md")]) == json.loads(text)
    # the manifest's Markdown also states the form in words the assistant can read
    assert "## How to answer" in as_md["manifest.md"] and "`tl apply` accepts" in as_md["manifest.md"]


def test_a_composed_graph_lends_its_clauses_in_a_file_of_their_source(composed_graph: Path, tmp_path: Path):
    files = _folder(composed_graph, tmp_path / "form")
    dump = json.loads(run(composed_graph, ["dump"], True))
    assert "source-src.json" in files
    clauses = json.loads(files["source-src.json"])["items"]
    assert [c["uid"] for c in clauses] == [i["uid"] for i in dump["items"] if i.get("source")]
    own = [i for name, text in files.items() if name not in ("manifest.json", "source-src.json")
           for i in json.loads(text)["items"]]
    assert sorted(i["uid"] for i in own) == sorted(i["uid"] for i in dump["items"] if not i.get("source"))
    manifest = json.loads(files["manifest.json"])
    assert any(f.get("source") == "src" for f in manifest["files"])
    assert manifest["composition"]["sources"][0]["namespace"] == "src"


def test_only_narrows_the_files_and_the_manifest_says_so(plain_graph: Path, tmp_path: Path):
    graph = load(plain_graph)
    sr1 = graph.by_register["SR"][0].uid
    files = _folder(plain_graph, tmp_path / "form", "--only", sr1)
    held = [i["uid"] for name, text in files.items() if name != "manifest.json" for i in json.loads(text)["items"]]
    assert held == [sr1]
    manifest = json.loads(files["manifest.json"])
    assert manifest["provenance"]["items"] == f"1 of {len(graph.items)}"


def test_the_form_is_a_folder_never_an_archive(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "form"
    assert main(["assistant", "-C", str(plain_graph), "-o", str(out), "--folder"]) == 0
    assert out.is_dir()
    assert main(["assistant", "-C", str(plain_graph), "-o", str(tmp_path / "again")]) == 0
    assert (tmp_path / "again").is_dir() and not list(tmp_path.glob("*.zip"))


def test_the_same_graph_gives_the_same_bytes(plain_graph: Path, tmp_path: Path):
    first = _folder(plain_graph, tmp_path / "a", "--repository", "x/y", "--ref", "main", "--commit", "0" * 40, "--tree", "clean")
    second = _folder(plain_graph, tmp_path / "b", "--repository", "x/y", "--ref", "main", "--commit", "0" * 40, "--tree", "clean")
    assert first == second


# --- SR-0018: the manifest -------------------------------------------------------


def test_the_manifest_names_what_the_folder_was_true_of_and_how_to_answer(git_graph: Path, tmp_path: Path):
    files = _folder(git_graph, tmp_path / "form")
    manifest = json.loads(files["manifest.json"])
    expected = provenance_of(git_graph, "x")
    assert manifest["throughline_assistant_form"] == FORM_VERSION
    assert manifest["provenance"]["repository"] == expected.repository == "example/fixture"
    assert manifest["provenance"]["ref"] == expected.ref
    assert manifest["provenance"]["commit"] == expected.commit and len(expected.commit) == 40
    assert manifest["provenance"]["tree"] == expected.tree
    assert manifest["tl"] == load(git_graph).tool_version
    assert {f["register"] for f in manifest["files"]} == {r.prefix for r in load(git_graph).registers}
    assert all((tmp_path / "form" / f"{f['file']}.json").is_file() for f in manifest["files"])
    assert manifest["instruction"] == INSTRUCTION
    assert "fingerprint" in manifest["instruction"] and "change set" in manifest["instruction"]
    # the form is the tool's own words, taken from the command, never written here
    assert manifest["change_set_format"] == change_set_format(git_graph, False)
    described = subprocess.run([str(Path(sys.executable).parent / "tl"), "apply", "--describe"],
                               capture_output=True, text=True, encoding="utf-8")
    assert manifest["change_set_format"] == described.stdout
    assert '"op": "amend"' in manifest["change_set_format"]
    assert "config" in manifest and "grounding" in manifest["config"]


def test_a_stated_provenance_is_written_as_given(plain_graph: Path, tmp_path: Path):
    files = _folder(plain_graph, tmp_path / "form", "--repository", "octo/graph", "--ref", "main",
                    "--commit", "f" * 40, "--tree", "dirty")
    manifest = json.loads(files["manifest.json"])
    assert manifest["provenance"] == {"repository": "octo/graph", "ref": "main", "commit": "f" * 40,
                                      "tree": "uncommitted changes", "tool": manifest["provenance"]["tool"]}
    assert "Working tree: uncommitted changes" in manifest["provenance_lines"]


def test_the_writer_reshapes_nothing(plain_graph: Path):
    dump = _dump(plain_graph)
    entries = dict(to_assistant(dump, PROV, "THE FORM"))
    assert set(entries) == {f"{r['prefix']}.json" for r in dump["registers"]} | {"manifest.json"}
    items = [i for name, data in entries.items() if name != "manifest.json" for i in json.loads(data)["items"]]
    assert sorted(items, key=lambda i: i["uid"]) == dump["items"]
    assert json.loads(entries["manifest.json"])["change_set_format"] == "THE FORM"
