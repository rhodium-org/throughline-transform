# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""Every format, over the fixture graphs, through the same path the CLI takes."""

from __future__ import annotations

import csv
import io
import re
import subprocess
import zipfile
from pathlib import Path

import pytest

from throughline_transform import markdown as md
from throughline_transform.blocks import as_blocks
from throughline_transform.cli import main, produce
from throughline_transform.html import to_html
from throughline_transform.model import register_titles, source_titles
from throughline_transform.notes import blocks_of, front_matter, note_name, to_notes, wikilink
from throughline_transform.office import column_name, sheet_name, to_docx, to_xlsx
from throughline_transform.project import TransformError, find_graph, is_composed, load
from throughline_transform.provenance import CLEAN, DIRTY, UNTRACKED, Provenance, provenance_of
from throughline_transform.tables import LINK_COLUMNS, cited_sources, links_of, per_register, to_csv, whole_graph

PROV = Provenance(repository="example/fixture", ref="main", commit="0" * 40, tree=CLEAN, tool="tl 2.2.0")


def _md(root: Path, **kw):
    graph = load(root)
    return graph, md.to_markdown(root, graph, md.Options(**kw), PROV)


# --- reaching the tool (SR-0001, SR-0002) -----------------------------------


def test_find_graph_refuses_a_directory_without_a_config(tmp_path: Path):
    with pytest.raises(TransformError):
        find_graph(tmp_path)


def test_find_graph_walks_up_from_a_subdirectory(plain_graph: Path, monkeypatch: pytest.MonkeyPatch):
    sub = plain_graph / "system-requirements"
    monkeypatch.chdir(sub)
    assert find_graph(None) == plain_graph.resolve()


def test_composition_is_decided_by_the_graph(plain_graph: Path, composed_graph: Path):
    assert not is_composed(plain_graph)
    assert is_composed(composed_graph)
    assert not load(plain_graph).composed
    assert load(composed_graph).composed


def test_dump_is_indexed(plain_graph: Path):
    graph = load(plain_graph)
    assert set(graph.by_register) == {"INT", "NG", "UR", "SR"}
    assert len(graph.items) == 7
    assert graph.borrowed == {}
    sr1 = graph.by_register["SR"][0]
    assert graph.incoming[sr1.uid] and {t for _, t in graph.incoming[sr1.uid]} == {"relates", "refines"}


def test_composed_dump_holds_borrowed_apart(composed_graph: Path):
    graph = load(composed_graph)
    assert len(graph.items) == 3
    assert "src:SR-0001" in graph.borrowed
    assert [s.namespace for s in graph.sources] == ["src"]


# --- markdown (SR-0002) -----------------------------------------------------


def test_markdown_is_written_by_the_tool(plain_graph: Path):
    graph, text = _md(plain_graph)
    assert text.startswith("# example/fixture — requirements")
    assert "- Working tree: clean" in text
    # A block this package has no code to produce is the evidence.
    for item in graph.items.values():
        assert f"**{item.uid} — " in text
    assert "<!-- tl:" not in text


def test_markdown_keeps_markers_when_asked(plain_graph: Path):
    _, text = _md(plain_graph, markers=True)
    assert "<!-- tl:catalog True -->" in text and "<!-- tl:end -->" in text


def test_markdown_options_change_the_document(plain_graph: Path):
    _, table = _md(plain_graph, body="table", stats=False)
    assert "## Items" in table and "## Every item" not in table and "## Summary" not in table
    _, matrix = _md(plain_graph, matrix=True)
    assert "## Traceability" in matrix and "### implements" in matrix and "### derives from" in matrix


def test_composed_markdown_mirrors_the_cited_clause(composed_graph: Path):
    _, text = _md(composed_graph)
    assert "## Clauses of adopted sources" in text
    assert "**src:SR-0001 — " in text
    assert "*Satisfies:* src:SR-0001" in text


# --- blocks and the document formats (SR-0008) -------------------------------


def test_blocks_read_the_shape_of_the_tools_output(plain_graph: Path):
    graph, text = _md(plain_graph)
    blocks = as_blocks(text, register_titles(graph), source_titles(graph))
    assert blocks[0].heading == 1
    assert any(b.front for b in blocks)
    groups = [b.text for b in blocks if b.group]
    # The catalogue is in UID order, so SR sorts before UR.
    assert groups == ["Intents", "Non-goals", "System requirements", "User requirements"]
    items = [b for b in blocks if b.item]
    assert len(items) == 7
    sr1 = next(b for b in items if b.item["uid"] == "SR-0001")
    assert sr1.heading == 4 and sr1.item["status"] == "draft"
    assert 'a colon, "quotes" & <angles>' in sr1.text
    quotes = [b for b in blocks if b.quote]
    assert any("The tool writes the Markdown." in b.text for b in quotes)
    assert any(b.small for b in blocks)


def test_composed_blocks_make_appendices(composed_graph: Path):
    graph, text = _md(composed_graph)
    blocks = as_blocks(text, register_titles(graph), source_titles(graph))
    appendix = next(b for b in blocks if b.group and b.text.startswith("Appendix A"))
    assert appendix.text == "Appendix A — src"
    assert appendix.subtitle and "plain" in appendix.subtitle


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert set(zf.namelist()) >= {"[Content_Types].xml", "word/document.xml", "word/styles.xml"}
        return zf.read("word/document.xml").decode("utf-8")


def test_docx_is_a_document_of_headings(plain_graph: Path):
    graph, text = _md(plain_graph, matrix=True, body="both")
    data = to_docx(as_blocks(text, register_titles(graph)))
    document = _docx_text(data)
    assert 'w:val="Heading2"' in document and 'w:val="Heading4"' in document
    assert "TOC \\o" in document
    assert "<w:tbl>" in document and "<w:tblHeader/>" in document
    assert "&lt;angles&gt;" in document and "&amp;" in document


def test_html_is_self_contained_and_escaped(plain_graph: Path):
    graph, text = _md(plain_graph)
    page = to_html(as_blocks(text, register_titles(graph)), PROV)
    assert page.startswith("<!doctype html>")
    assert "<style>" in page and "@page" in page
    assert '<nav class="contents">' in page and 'href="#h-' in page
    assert "&lt;angles&gt;" in page and "<angles>" not in page
    assert page.count('<section class="item">') == 7
    assert "Working tree: clean" in page


# --- tables (SR-0005, SR-0006, SR-0007) -------------------------------------


def test_whole_graph_is_one_row_per_item_over_declared_columns(plain_graph: Path):
    graph = load(plain_graph)
    table = whole_graph(graph)
    assert table.columns[:8] == ["uid", "register", "type", "status", "title", "text", "rationale", "normative"]
    assert "priority" in table.columns and "verification" in table.columns
    assert table.link_types == ["derives_from", "implements", "refines", "relates"]
    assert len(table.rows) == 7
    row = next(r for r in table.rows if r[0] == "SR-0002")
    assert row[table.columns.index("relates")] == "SR-0001"


def test_per_register_carries_only_its_own_columns(plain_graph: Path):
    tables = per_register(load(plain_graph))
    # In the order the tool declares its registers.
    assert sorted(t.name for t in tables) == ["Intents", "Non-goals", "System requirements", "User requirements"]
    intents = next(t for t in tables if t.name == "Intents")
    assert "priority" not in intents.columns


def test_links_table_names_the_sheet_at_each_end(plain_graph: Path, composed_graph: Path):
    graph = load(plain_graph)
    tables = per_register(graph)
    links = links_of(tables)
    assert links.columns == LINK_COLUMNS
    assert ["System requirements", "SR-0002", "relates", "System requirements", "SR-0001"] in links.rows
    assert ["User requirements", "UR-0001", "derives_from", "Intents", "INT-0001"] in links.rows
    borrowed = links_of([whole_graph(load(composed_graph))])
    assert ["All items", "SR-0001", "satisfies", "src", "src:SR-0001"] in borrowed.rows


def test_cited_sources_hold_only_what_is_cited(composed_graph: Path):
    tables = cited_sources(load(composed_graph))
    assert [t.name for t in tables] == ["src"]
    assert [r[0] for r in tables[0].rows] == ["src:SR-0001"]
    assert cited_sources(load(composed_graph.parent / "consumer")) == tables


def test_csv_quotes_every_field(plain_graph: Path):
    text = to_csv(whole_graph(load(plain_graph)))
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0][0] == "uid"
    assert len({len(r) for r in rows}) == 1
    assert any("\n" in cell for row in rows for cell in row)  # the two-line text survived quoting


def test_xlsx_is_read_only_and_sortable(plain_graph: Path):
    graph = load(plain_graph)
    data = to_xlsx([whole_graph(graph), links_of([whole_graph(graph)])])
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        workbook = zf.read("xl/workbook.xml").decode()
        sheet = zf.read("xl/worksheets/sheet1.xml").decode()
        assert zf.testzip() is None
    assert 'readOnlyRecommended="1"' in workbook and 'lockStructure="1"' in workbook
    assert '<sheet name="All items"' in workbook and '<sheet name="Links"' in workbook
    assert 'sort="0"' in sheet and "<autoFilter" in sheet and 'state="frozen"' in sheet


def test_sheet_and_column_names():
    assert column_name(0) == "A" and column_name(25) == "Z" and column_name(26) == "AA" and column_name(701) == "ZZ"
    assert sheet_name("a/b?c*d[e]f:g", 0) == "a b c d e f g"
    assert sheet_name("", 2) == "Sheet3"
    assert len(sheet_name("x" * 40, 0)) == 31


# --- notes (SR-0009) ---------------------------------------------------------


def test_notes_are_one_per_item_with_front_matter_and_links(plain_graph: Path):
    graph, text = _md(plain_graph, stats=False)
    entries = dict(to_notes(text, graph, PROV))
    assert "About this export.md" in entries
    assert "System requirements/SR-0001.md" in entries and "Intents/INT-0001.md" in entries
    sr2 = entries["System requirements/SR-0002.md"].decode()
    assert sr2.startswith('---\nuid: "SR-0002"\n')
    assert 'priority: "should"' in sr2 and '  - "type/system_requirement"' in sr2 and '  - "status/draft"' in sr2
    assert "*Relates:* [[SR-0001]]" in sr2
    assert "*Implements:* [[UR-0002]]" in sr2
    # The TOML table in prose is escaped rather than becoming a ghost note. The
    # title in the front matter is a quoted YAML string, which the note tool
    # reads as a property, not as a link.
    body = sr2.split("\n---\n", 1)[1]
    assert "\\[\\[sources\\]\\]" in body and "[[sources]]" not in body
    # Every wikilink in a note's body names a note. The front matter is data,
    # not prose: a title there is a quoted string the note tool never follows.
    names = {Path(p).stem for p in entries}
    for path, data in entries.items():
        note_body = data.decode().split("\n---\n", 1)[-1]
        for target in re.findall(r"(?<!\\)\[\[([^\]|]+)", note_body):
            assert target in names, f"{path} links to {target}"


def test_notes_never_link_to_themselves(plain_graph: Path):
    graph, text = _md(plain_graph, stats=False)
    for path, data in to_notes(text, graph, PROV):
        stem = Path(path).stem.replace(" ", ":")
        assert f"[[{stem}]]" not in data.decode(), path


def test_borrowed_clause_notes_replace_the_colon(composed_graph: Path):
    graph, text = _md(composed_graph, stats=False)
    entries = dict(to_notes(text, graph, PROV, folder="vault"))
    assert "vault/sources/src/src SR-0001.md" in entries
    clause = entries["vault/sources/src/src SR-0001.md"].decode()
    assert 'uid: "src:SR-0001"' in clause and 'source: "src"' in clause
    citing = entries["vault/System requirements/SR-0001.md"].decode()
    assert "[[src SR-0001|src:SR-0001]]" in citing
    assert note_name("asvs:SR-0255") == "asvs SR-0255"


def test_front_matter_quotes_what_could_change_the_shape(plain_graph: Path):
    graph = load(plain_graph)
    item = graph.items["SR-0001"]
    fm = front_matter(item, "SR-0001")
    assert 'a colon, \\"quotes\\" & <angles>"' in fm
    assert "normative: true" in fm
    assert wikilink("see SR-0001 and SR-0009", "X", {"SR-0001": "SR-0001"}) == "see [[SR-0001]] and SR-0009"


def test_blocks_of_cuts_at_the_item_line(composed_graph: Path):
    _, text = _md(composed_graph, stats=False)
    blocks = blocks_of(text)
    assert [b.id for b in blocks] == ["INT-0001", "SR-0001", "UR-0001", "src:SR-0001"]
    assert [b.borrowed for b in blocks] == [False, False, False, True]


# --- provenance (SR-0004) ----------------------------------------------------


def test_provenance_outside_version_control(plain_graph: Path):
    p = provenance_of(plain_graph, "tl 2.2.0")
    assert p.repository == "plain" and p.ref == "" and p.commit == "" and p.tree == UNTRACKED
    assert "Working tree: not under version control" in p.lines()
    assert p.stem == "plain"


def test_provenance_reads_git_and_notices_uncommitted_changes(git_graph: Path):
    clean = provenance_of(git_graph, "tl 2.2.0")
    assert clean.repository == "example/fixture" and clean.ref == "main" and len(clean.commit) == 40
    assert clean.tree == CLEAN
    assert clean.stem == "example-fixture-main"
    (git_graph / "intents" / "INT-0001.yml").write_text(
        (git_graph / "intents" / "INT-0001.yml").read_text() + "# touched\n"
    )
    dirty = provenance_of(git_graph, "tl 2.2.0")
    assert dirty.tree == DIRTY and dirty.commit == clean.commit
    subprocess.run(["git", "-C", str(git_graph), "checkout", "--", "."], check=True)


# --- the command (UR-0001, SR-0011) -----------------------------------------


@pytest.mark.parametrize("fmt", ["md", "notes", "csv", "xlsx", "docx", "html"])
def test_every_format_writes_a_file(plain_graph: Path, tmp_path: Path, fmt: str, capsys: pytest.CaptureFixture):
    out = tmp_path / f"out.{fmt}"
    assert main([fmt, "-C", str(plain_graph), "-o", str(out)]) == 0
    assert out.is_file() and out.stat().st_size > 0
    line = capsys.readouterr().out
    assert str(out) in line and "not under version control" in line
    if fmt in ("notes", "csv", "xlsx", "docx"):
        with zipfile.ZipFile(out) as zf:
            assert zf.testzip() is None
            for info in zf.infolist():
                assert info.date_time == (1980, 1, 1, 0, 0, 0)


def test_default_names_come_from_the_graph(plain_graph: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    assert main(["xlsx", "-C", str(plain_graph)]) == 0
    assert (tmp_path / "plain.xlsx").is_file()
    assert main(["notes", "-C", str(plain_graph)]) == 0
    assert (tmp_path / "plain-notes.zip").is_file()


def test_folder_output_unpacks_the_vault(plain_graph: Path, tmp_path: Path):
    target = tmp_path / "vault"
    assert main(["notes", "-C", str(plain_graph), "-o", str(target), "--folder"]) == 0
    assert (target / "About this export.md").is_file()
    assert (target / "System requirements" / "SR-0001.md").is_file()
    assert main(["csv", "-C", str(plain_graph), "-o", str(tmp_path / "csv"), "--folder", "--split", "per-register"]) == 0
    assert (tmp_path / "csv" / "links.csv").is_file() and (tmp_path / "csv" / "Intents.csv").is_file()


def test_folder_is_refused_for_a_single_file_format(plain_graph: Path):
    with pytest.raises(SystemExit) as exc:
        main(["xlsx", "-C", str(plain_graph), "--folder"])
    assert exc.value.code == 2


def test_a_wrong_directory_is_one_line_on_stderr(tmp_path: Path, capsys: pytest.CaptureFixture):
    assert main(["md", "-C", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("tl-transform: ") and "throughline.toml" in err


def test_same_graph_twice_is_the_same_bytes(plain_graph: Path):
    graph = load(plain_graph)
    opts = md.Options()
    first, _ = produce(graph, plain_graph, "xlsx", opts, PROV)
    second, _ = produce(graph, plain_graph, "xlsx", opts, PROV)
    assert first == second
    notes_a, _ = produce(graph, plain_graph, "notes", opts, PROV)
    notes_b, _ = produce(graph, plain_graph, "notes", opts, PROV)
    assert notes_a == notes_b
