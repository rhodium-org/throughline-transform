# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The Markdown, as the blocks a document is made of (SR-0008).

Deliberately shallow. This reads the headings and paragraphs out of what the
tool wrote rather than interpreting Markdown properly — a full parser here
would be a second opinion about a document the tool already rendered.

What it adds is structure the tool's Markdown states only by shape: an item's
opening line becomes a heading with its type and status beneath, items are
grouped under a section per register (or per source, in the mirrored clauses),
and the attribute line is marked as the small print it is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .shape import ATTRS_LINE, ITEM_LINE


@dataclass
class Block:
    text: str
    #: 1–4 for a heading; ``None`` for body text.
    heading: int | None = None
    #: Rendered as a quotation, which is how an item's own words are set.
    quote: bool = False
    #: The tool's attribute line — small print beneath an item.
    small: bool = False
    #: Front matter: the provenance lines before the first section.
    front: bool = False
    #: A heading that opens a register's or a source's group of items.
    group: bool = False
    #: A line beneath a heading saying where an appendix's source comes from.
    subtitle: str | None = None
    #: A heading that opens one item: ``{"uid", "type", "status"}``.
    item: dict[str, str] | None = None
    #: A table the tool wrote, kept as a table: ``{"header": [...], "rows": [[...]]}``.
    table: dict[str, list] | None = None
    #: The contents entries beneath this heading, filled by the writers that need them.
    children: list["Block"] = field(default_factory=list, repr=False)


_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")


def strip(text: str) -> str:
    """Drop the emphasis marks a document has no use for, keeping the words."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text.replace("`", "")


def _is_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|") and len(line) > 2


def _cells(row: str) -> list[str]:
    return [strip(cell.strip()) for cell in row[1:-1].split("|")]


def as_blocks(
    markdown: str,
    registers: dict[str, str] | None = None,
    sources: dict[str, str] | None = None,
) -> list[Block]:
    registers = registers or {}
    sources = sources or {}
    blocks: list[Block] = []
    lines = markdown.split("\n")
    group: str | None = None
    front = True
    in_sources = False
    appendices = 0

    i = 0
    while i < len(lines):
        text = lines[i].strip()
        i += 1
        if not text:
            continue
        # A region marker is instruction to the tool, not something to read.
        if text.startswith("<!--"):
            continue

        item = ITEM_LINE.match(text)
        if item:
            uid, ref, title, type_, status = item.groups()
            colon = uid.find(":")
            prefix = uid[: uid.rfind("-")] if colon == -1 else uid[:colon]
            if prefix != group:
                group = prefix
                if in_sources:
                    letter = chr(65 + (appendices % 26))
                    appendices += 1
                    blocks.append(
                        Block(
                            heading=2,
                            text=f"Appendix {letter} — {prefix}",
                            group=True,
                            subtitle=sources.get(prefix),
                        )
                    )
                else:
                    blocks.append(Block(heading=3, text=registers.get(prefix, prefix), group=True))
            blocks.append(
                Block(
                    heading=3 if in_sources else 4,
                    text=f"{uid}{f' ({ref})' if ref else ''} — {strip(title)}",
                    item={"uid": uid, "type": type_, "status": status},
                )
            )
            continue

        if _is_row(text):
            rows: list[list[str]] = []
            i -= 1
            while i < len(lines) and _is_row(lines[i].strip()):
                row = lines[i].strip()
                if not re.match(r"^\|[\s:|-]+\|$", row):
                    rows.append(_cells(row))
                i += 1
            if rows:
                blocks.append(Block(text="", table={"header": rows[0], "rows": rows[1:]}))
            continue

        heading = _HEADING.match(text)
        if heading:
            level = len(heading.group(1))
            if level >= 2:
                front = False
            group = None
            in_sources = level == 2 and bool(re.search(r"adopted sources", heading.group(2), re.I))
            if in_sources:
                blocks.append(Block(heading=2, text="Appendices"))
                blocks.append(
                    Block(
                        text=(
                            "The clauses of the adopted sources that this intent graph cites, "
                            "one appendix per source, in the words the source states them."
                        )
                    )
                )
                continue
            blocks.append(Block(heading=level, text=strip(heading.group(2))))
            continue
        if text.startswith(">"):
            blocks.append(Block(quote=True, text=strip(re.sub(r"^>\s?", "", text))))
            continue
        if ATTRS_LINE.match(text):
            blocks.append(Block(text=strip(text), small=True))
            continue
        blocks.append(Block(text=strip(re.sub(r"^[-*]\s+", "", text)), front=front))
    return blocks
