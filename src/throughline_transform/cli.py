# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""``tl-transform``: a graph on disk, in the form a reader opens (UR-0001, UR-0002).

    tl-transform md        [-C DIR] [-o FILE] [--body …] [--matrix] [--no-stats] [--markers]
    tl-transform notes     [-C DIR] [-o FILE|DIR] [--folder]
    tl-transform csv       [-C DIR] [-o FILE|DIR] [--folder] [--split …]
    tl-transform xlsx      [-C DIR] [-o FILE] [--split …]
    tl-transform docx      [-C DIR] [-o FILE] [--body …] [--matrix] [--no-stats]
    tl-transform html      [-C DIR] [-o FILE] [--body …] [--matrix] [--no-stats]

Exit codes: 0 written · 1 the tool or the file system refused · 2 usage.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from throughline.version import distribution_version as _v

from . import markdown as md
from .blocks import as_blocks
from .html import to_html
from .model import Graph, register_titles, source_titles
from .notes import to_notes
from .office import to_docx, to_xlsx
from .package import Entry, archive, unpack, utf8
from .project import TransformError, find_graph, load
from .provenance import Provenance, provenance_of
from .tables import Table, cited_sources, file_name, links_of, per_register, to_csv, whole_graph

FORMATS = ("md", "notes", "csv", "xlsx", "docx", "html")
PROSE = ("md", "docx", "html")
FOLDERS = ("notes", "csv")


def version_string() -> str:
    return (
        f"tl-transform {_v('throughline-transform')} "
        f"(throughline-compose {_v('throughline-compose')}, throughline {_v('throughline')})"
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tl-transform",
        description="Turn a throughline graph on disk, committed or not, into the form a reader opens.",
    )
    p.add_argument("--version", action="version", version=version_string())
    p.add_argument("format", choices=FORMATS, help="what to produce")
    p.add_argument("-C", dest="directory", metavar="DIR", help="the directory holding throughline.toml")
    p.add_argument("-o", dest="output", metavar="PATH", help="where to write; a name is chosen from the graph if omitted")
    p.add_argument("--folder", action="store_true", help="notes, csv: write the files into a folder instead of a zip")
    p.add_argument(
        "--body",
        choices=("catalog", "table", "both"),
        default="catalog",
        help="md, docx, html: every item in full, a table of items, or both",
    )
    p.add_argument("--matrix", action="store_true", help="md, docx, html: add a traceability matrix per grounding link")
    p.add_argument("--no-stats", dest="stats", action="store_false", help="md, docx, html: leave out the tool's summary")
    p.add_argument("--markers", action="store_true", help="md: keep the tool's region markers so `tl docs` can refill the file")
    p.add_argument(
        "--split",
        choices=("one", "per-register"),
        default="one",
        help="csv, xlsx: one table of everything, or one per register",
    )
    return p


def _tables(graph: Graph, split: str) -> tuple[list[Table], Table, list[Table]]:
    tables = per_register(graph) if split == "per-register" else [whole_graph(graph)]
    return tables, links_of(tables), cited_sources(graph)


def _about(provenance: Provenance, extra: list[list[str]] | None = None) -> Table:
    rows = [line.split(": ", 1) for line in provenance.lines()]
    return Table(name="About this export", columns=["Field", "Value"], rows=rows + (extra or []))


def produce(graph: Graph, root: Path, fmt: str, opts: md.Options, provenance: Provenance) -> tuple[bytes | list[Entry], str]:
    """The output and its default file name; a list of entries for the folder formats."""
    stem = provenance.stem
    if fmt in PROSE:
        text = md.to_markdown(root, graph, opts, provenance)
        if fmt == "md":
            return utf8(text), f"{stem}.md"
        blocks = as_blocks(text, register_titles(graph), source_titles(graph))
        if fmt == "docx":
            return to_docx(blocks), f"{stem}.docx"
        return utf8(to_html(blocks, provenance)), f"{stem}.html"

    if fmt == "notes":
        text = md.to_markdown(
            root, graph, replace(opts, body="catalog", matrix=False, stats=False, markers=False), provenance
        )
        return to_notes(text, graph, provenance), f"{stem}-notes"

    tables, links, sources = _tables(graph, opts.split)
    if fmt == "xlsx":
        return to_xlsx([*tables, links, *sources, _about(provenance)]), f"{stem}.xlsx"

    about = _about(
        provenance,
        [["Read-only", "No. csv cannot be protected; the xlsx output of the same graph is."]],
    )
    entries: list[Entry] = [(file_name(t), utf8(to_csv(t))) for t in tables]
    entries.append(("links.csv", utf8(to_csv(links))))
    entries += [(f"{t.name}.csv", utf8(to_csv(t))) for t in sources]
    entries.append(("about-this-export.csv", utf8(to_csv(about))))
    return entries, f"{stem}-csv"


def write(result: bytes | list[Entry], default: str, output: str | None, folder: bool) -> Path:
    if isinstance(result, bytes):
        target = Path(output) if output else Path(default)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        return target
    if folder:
        target = Path(output) if output else Path(default)
        unpack(result, target)
        return target
    target = Path(output) if output else Path(f"{default}.zip")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(archive(result))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.folder and args.format not in FOLDERS:
        parser.error(f"--folder applies to {' and '.join(FOLDERS)}, not {args.format}")
    opts = md.Options(body=args.body, matrix=args.matrix, stats=args.stats, markers=args.markers, split=args.split)
    try:
        root = find_graph(args.directory)
        graph = load(root)
        provenance = provenance_of(root, graph.tool_version)
        result, default = produce(graph, root, args.format, opts, provenance)
        target = write(result, default, args.output, args.folder)
    except (TransformError, OSError, ValueError) as exc:
        print(f"tl-transform: {exc}", file=sys.stderr)
        return 1
    count = "" if isinstance(result, bytes) else f" ({len(result)} files)"
    print(f"{target}{count} — {provenance.repository}, {provenance.tree}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
