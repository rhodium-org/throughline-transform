# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The graph as rows and columns (SR-0005, SR-0006, SR-0007).

csv and xlsx exist to be sorted, filtered and counted, so an item is a row. The
columns are the ones the graph itself declares — read from the tool's export,
never a list fixed here — so a graph carrying an attribute this package has
never heard of exports it too.

Links are flattened into one column per link type on the item's row, and given
again as a table of their own, one row per link, because a reviewer uses them
both ways.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Graph, Item, is_borrowed, prefix_of, split_borrowed

#: The fields every item has, in the order a reader expects to meet them.
FIXED = ["uid", "register", "type", "status", "title", "text", "rationale", "normative"]

#: The links table's columns, in the order SR-0006 states them.
LINK_COLUMNS = ["from sheet", "from uid", "link type", "to sheet", "to uid"]
LINKS_TABLE = "Links"


@dataclass
class Table:
    name: str
    columns: list[str]
    rows: list[list[str]]
    #: Which of the columns past the fixed ones are link types, not attributes.
    link_types: list[str] = field(default_factory=list)


def cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _columns_for(items: list[Item]) -> tuple[list[str], list[str]]:
    attrs: set[str] = set()
    links: set[str] = set()
    for item in items:
        attrs.update(item.attrs.keys())
        links.update(link.type for link in item.links)
    return sorted(attrs), sorted(links)


def _row_for(item: Item, attrs: list[str], links: list[str]) -> list[str]:
    by_type: dict[str, list[str]] = {}
    for link in item.links:
        by_type.setdefault(link.type, []).append(link.target)
    return [
        item.uid,
        prefix_of(item.uid),
        item.type,
        item.status,
        item.title,
        item.text or "",
        item.rationale or "",
        cell(item.normative),
        *[cell(item.attrs.get(name)) for name in attrs],
        # Several targets of one type share a cell, because splitting them into
        # rows would stop an item being a row.
        *[", ".join(by_type.get(link_type, [])) for link_type in links],
    ]


def _table_of(items: list[Item], name: str) -> Table:
    attrs, links = _columns_for(items)
    return Table(
        name=name,
        columns=[*FIXED, *attrs, *links],
        rows=[_row_for(item, attrs, links) for item in items],
        link_types=links,
    )


def whole_graph(graph: Graph) -> Table:
    """Every item in one table, in UID order."""
    return _table_of(sorted(graph.items.values(), key=lambda i: i.uid), "All items")


def per_register(graph: Graph) -> list[Table]:
    """One table per register that holds items, with only the columns its own items use."""
    titles = {r.prefix: r.title for r in graph.registers}
    return [
        _table_of(items, titles.get(prefix, prefix))
        for prefix, items in graph.by_register.items()
        if items
    ]


def cited_sources(graph: Graph) -> list[Table]:
    """The clauses of adopted sources the graph cites, one table per source (SR-0007).

    Only what some item links to, whatever the link type. Columns come from the
    clauses themselves, so each source keeps its own vocabulary.
    """
    cited: dict[str, list[Item]] = {}
    seen: set[str] = set()
    for item in graph.items.values():
        for link in item.links:
            if not is_borrowed(link.target) or link.target in seen:
                continue
            clause = graph.borrowed.get(link.target)
            if clause is None:
                continue
            seen.add(link.target)
            namespace, _ = split_borrowed(link.target)
            cited.setdefault(namespace, []).append(clause)
    return [
        _table_of(sorted(clauses, key=lambda i: i.uid), namespace)
        for namespace, clauses in sorted(cited.items())
    ]


def links_of(tables: list[Table]) -> Table:
    """Every link as a row of its own (SR-0006).

    The item tables are read, not the graph: the links table names each end by
    the sheet its row is on in this export, which depends on how the export was
    split. A link into an adopted source names the namespace as the sheet.
    """
    sheet_of: dict[str, str] = {}
    for table in tables:
        for row in table.rows:
            sheet_of[row[0]] = table.name
    link_columns = {name for table in tables for name in table.link_types}
    rows: list[list[str]] = []
    for table in tables:
        uid_column = table.columns.index("uid")
        for row in table.rows:
            source = row[uid_column]
            for c in range(len(FIXED), len(table.columns)):
                link_type = table.columns[c]
                if not row[c] or link_type not in link_columns:
                    continue
                for target in row[c].split(", "):
                    home = sheet_of.get(target)
                    to_sheet = home if home is not None else (target.split(":")[0] if ":" in target else "")
                    rows.append([table.name, source, link_type, to_sheet, target])
    return Table(name=LINKS_TABLE, columns=list(LINK_COLUMNS), rows=rows)


def to_csv(table: Table) -> str:
    """One table as csv (RFC 4180), every field quoted."""

    def quote(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    lines = [",".join(quote(c) for c in table.columns)]
    lines += [",".join(quote(v) for v in row) for row in table.rows]
    return "\r\n".join(lines) + "\r\n"


def file_name(table: Table) -> str:
    """A csv file name for the table, with the characters a file name cannot hold removed."""
    return "".join(ch for ch in table.name if ch.isalnum() or ch in " -_") + ".csv"
