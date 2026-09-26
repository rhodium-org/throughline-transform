# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""An output of only the items its caller names (UR-0007, SR-0016).

The plain fixture holds seven items. Two are named here, UR-0002 and SR-0002,
in two --only flags: SR-0002 implements UR-0002, so exactly one link has both
ends in the output, while SR-0002 also relates to SR-0001, UR-0002 derives from
INT-0001 and SR-0003 implements UR-0002 — three links with one end left out.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import pytest

from throughline_transform.cli import main

ONLY = ["--only", "UR-0002", "--only", "SR-0002"]
HELD = {"UR-0002", "SR-0002"}


def _rows(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8"))))


def test_the_markdown_holds_the_named_items_and_says_so(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "only.md"
    assert main(["md", "-C", str(plain_graph), "-o", str(out), "--matrix", "--body", "both", *ONLY]) == 0
    text = out.read_text(encoding="utf-8")
    assert "- Items: 2 of 7" in text
    # Written by tl docs, catalogue and table alike: the two named, and no other.
    assert set(re.findall(r"^\*\*([A-Z]+-\d{4}) — ", text, re.M)) == HELD
    table = text.split("## Items", 1)[1].split("##", 1)[0]
    assert set(re.findall(r"^\| ([A-Z]+-\d{4}) \|", table, re.M)) == HELD
    # Each matrix has rows only for what is held: UR-0002's realizers, and no intent.
    implements = text.split("### implements", 1)[1].split("##", 1)[0]
    assert set(re.findall(r"^\| ([A-Z]+-\d{4}) \|", implements, re.M)) == {"UR-0002"}
    derives = text.split("### derives from", 1)[1].split("##", 1)[0]
    assert re.findall(r"^\| ([A-Z]+-\d{4}) \|", derives, re.M) == []
    assert "- **Items:** 2 — " in text


def test_the_tables_hold_the_named_rows_and_only_the_links_between_them(plain_graph: Path, tmp_path: Path):
    target = tmp_path / "csv"
    assert main(["csv", "-C", str(plain_graph), "-o", str(target), "--folder", *ONLY]) == 0
    items = _rows((target / "All items.csv").read_bytes())
    assert {row[0] for row in items[1:]} == HELD
    links = _rows((target / "links.csv").read_bytes())
    assert links[1:] == [["All items", "SR-0002", "implements", "All items", "UR-0002"]]
    about = dict(tuple(row) for row in _rows((target / "about-this-export.csv").read_bytes())[1:])
    assert about["Items"] == "2 of 7"

    split = tmp_path / "split"
    assert main(["csv", "-C", str(plain_graph), "-o", str(split), "--folder", "--split", "per-register", *ONLY]) == 0
    # A register holding nothing named is no table at all.
    assert sorted(p.name for p in split.iterdir()) == [
        "System requirements.csv", "User requirements.csv", "about-this-export.csv", "links.csv",
    ]
    assert _rows((split / "links.csv").read_bytes())[1:] == [
        ["System requirements", "SR-0002", "implements", "User requirements", "UR-0002"],
    ]


def test_the_workbook_holds_two_item_rows_and_one_link(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "only.xlsx"
    assert main(["xlsx", "-C", str(plain_graph), "-o", str(out), *ONLY]) == 0
    with zipfile.ZipFile(out) as zf:
        workbook = zf.read("xl/workbook.xml").decode()
        names = re.findall(r'<sheet name="([^"]+)"', workbook)
        sheets = {name: zf.read(f"xl/worksheets/sheet{i + 1}.xml").decode() for i, name in enumerate(names)}
    # A header row, then one row per item or link.
    assert sheets["All items"].count("<row ") == 3
    assert sheets["Links"].count("<row ") == 2
    # The workbook writes its strings inline, so the About sheet reads as written.
    assert ">Items</t>" in sheets["About this export"] and ">2 of 7</t>" in sheets["About this export"]


def test_the_notes_hold_the_named_items_and_link_to_nothing_left_out(plain_graph: Path, tmp_path: Path):
    target = tmp_path / "vault"
    assert main(["notes", "-C", str(plain_graph), "-o", str(target), "--folder", *ONLY]) == 0
    notes = sorted(str(p.relative_to(target)) for p in target.rglob("*.md"))
    assert notes == ["About this export.md", "System requirements/SR-0002.md", "User requirements/UR-0002.md"]
    for path in notes:
        body = (target / path).read_text(encoding="utf-8").split("\n---\n", 1)[-1]
        for linked in re.findall(r"(?<!\\)\[\[([^\]|]+)", body):
            assert linked in HELD, f"{path} links to {linked}"
    sr2 = (target / "System requirements/SR-0002.md").read_text(encoding="utf-8")
    assert "*Implements:* [[UR-0002]]" in sr2 and "*Relates:* SR-0001" in sr2
    ur2 = (target / "User requirements/UR-0002.md").read_text(encoding="utf-8")
    assert "*Implements this:* [[SR-0002]]" in ur2 and "SR-0003" not in ur2
    about = (target / "About this export.md").read_text(encoding="utf-8")
    assert "- Items: 2 of 7" in about and "This export holds 2 items." in about


def test_the_blocks_and_documents_say_what_they_hold(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "only.json"
    assert main(["blocks", "-C", str(plain_graph), "-o", str(out), *ONLY]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["provenance"]["items"] == "2 of 7"
    assert doc["provenance_lines"][-1] == "Items: 2 of 7"
    assert {b["item"]["uid"] for b in doc["blocks"] if "item" in b} == HELD
    for fmt in ("docx", "html"):
        target = tmp_path / f"only.{fmt}"
        assert main([fmt, "-C", str(plain_graph), "-o", str(target), *ONLY]) == 0
        data = target.read_bytes()
        text = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode() if fmt == "docx" else data.decode()
        assert "Items: 2 of 7" in text
        assert "SR-0002" in text and "SR-0003" not in text


def test_a_composed_output_mirrors_only_what_the_named_items_cite(composed_graph: Path, tmp_path: Path):
    citing = tmp_path / "citing.md"
    assert main(["md", "-C", str(composed_graph), "-o", str(citing), "--only", "SR-0001"]) == 0
    assert "**src:SR-0001 — " in citing.read_text(encoding="utf-8")
    other = tmp_path / "other.md"
    assert main(["md", "-C", str(composed_graph), "-o", str(other), "--only", "UR-0001"]) == 0
    assert "**src:SR-0001 — " not in other.read_text(encoding="utf-8")
    target = tmp_path / "csv"
    assert main(["csv", "-C", str(composed_graph), "-o", str(target), "--folder", "--only", "UR-0001"]) == 0
    assert not (target / "src.csv").exists()


def test_an_identifier_the_graph_lacks_is_refused_and_nothing_is_written(
    plain_graph: Path, tmp_path: Path, capsys: pytest.CaptureFixture
):
    out = tmp_path / "never.md"
    with pytest.raises(SystemExit) as exc:
        main(["md", "-C", str(plain_graph), "-o", str(out), "--only", "SR-0002,SR-0099,NOPE-1"])
    assert exc.value.code == 2
    assert "SR-0099, NOPE-1" in capsys.readouterr().err
    assert not out.exists()
    with pytest.raises(SystemExit) as exc:
        main(["md", "-C", str(plain_graph), "-o", str(out), "--only", " , "])
    assert exc.value.code == 2
    assert not out.exists()


def test_named_nothing_an_output_says_nothing_more(plain_graph: Path, tmp_path: Path):
    out = tmp_path / "all.json"
    assert main(["blocks", "-C", str(plain_graph), "-o", str(out)]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert "items" not in doc["provenance"]
    assert not any(line.startswith("Items:") for line in doc["provenance_lines"])
    assert len([b for b in doc["blocks"] if "item" in b]) == 7
