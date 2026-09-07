# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The graph as a folder of notes (SR-0009).

A note-taking tool such as Obsidian opens a folder of Markdown files as a
vault, follows ``[[wikilinks]]`` between them in both directions and draws the
graph they make. This output is that folder: one note per item, one per cited
clause of an adopted source, and an About note carrying the provenance.

The prose is the tool's. The catalogue is written once and cut here at the
item line, so the words in a note are the words ``tl docs`` publishes. What is
added is what the tool has no view on: file boundaries, YAML front matter the
note tool reads as properties, link syntax, and the body reshaped for a note —
the item line as the note's heading, the attribute line left to the front
matter, and the incoming links written out so a reader sees what rests on the
item without opening a pane (SR-0009, reversed on first use in Obsidian).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .model import Graph, Item, prefix_of, split_borrowed
from .package import Entry, utf8
from .provenance import Provenance
from .shape import ATTRS_LINE, IDENTIFIER, ITEM_LINE

_HEADING = re.compile(r"^#{1,3}\s+(.*)$")


@dataclass
class NoteBlock:
    #: The identifier the tool wrote — namespace-qualified for a clause.
    id: str
    #: Every line of the block, the head line first, exactly as written.
    lines: list[str] = field(default_factory=list)
    #: Whether the block came from the mirrored clauses of adopted sources.
    borrowed: bool = False


def blocks_of(markdown: str) -> list[NoteBlock]:
    """Cut the tool's document into its item blocks.

    Which section a block sits in is what says whether it is the graph's own
    item or a clause mirrored from a source: the composer qualifies a clause's
    identifier, but the section is the boundary the tool itself drew.
    """
    blocks: list[NoteBlock] = []
    borrowed = False
    current: NoteBlock | None = None
    for raw in markdown.split("\n"):
        line = raw.rstrip()
        heading = _HEADING.match(line)
        if heading:
            current = None
            borrowed = bool(re.search(r"adopted sources", heading.group(1), re.I))
            continue
        head = ITEM_LINE.match(line)
        if head:
            current = NoteBlock(id=head.group(1), lines=[line], borrowed=borrowed)
            blocks.append(current)
            continue
        if current is not None:
            current.lines.append(line)
    for block in blocks:
        while block.lines and not block.lines[-1]:
            block.lines.pop()
    return blocks


def note_name(identifier: str) -> str:
    """What a note is called.

    A note tool links by name, so every name in the vault has to be unique, and
    refuses a colon in one. A clause keeps its namespace so it cannot collide
    with a local item of the same number, with the colon replaced by a space.
    """
    return identifier.replace(":", " ")


def file_safe(text: str) -> str:
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", text).strip() or "untitled"


def _folder_of(block: NoteBlock, registers: dict[str, str]) -> str:
    if block.borrowed:
        namespace, _ = split_borrowed(block.id)
        return f"sources/{file_safe(namespace)}"
    prefix = prefix_of(block.id)
    return file_safe(registers.get(prefix, prefix))


def scalar(value: object) -> str:
    """A YAML scalar the note tool reads back as what it was.

    Every string is double-quoted through JSON, which is a valid YAML
    double-quoted scalar, so a title holding a colon or a hash cannot change
    the document's shape.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return '""'
    return json.dumps(str(value), ensure_ascii=False)


def _key(name: str) -> str:
    return name if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*$", name) else json.dumps(name)


def front_matter(item: Item, identifier: str, reference: str | None = None) -> str:
    lines = ["---", f"uid: {scalar(identifier)}"]
    if reference:
        lines.append(f"reference: {scalar(reference)}")
    if item.source:
        lines.append(f"source: {scalar(item.source)}")
    lines += [f"type: {scalar(item.type)}", f"status: {scalar(item.status)}"]
    if item.normative is not None:
        lines.append(f"normative: {scalar(item.normative)}")
    for name, value in item.attrs.items():
        if isinstance(value, list):
            lines.append(f"{_key(name)}:")
            lines += [f"  - {scalar(v)}" for v in value]
        else:
            lines.append(f"{_key(name)}: {scalar(value)}")
    lines += ["aliases:", f"  - {scalar(item.title)}"]
    lines += ["tags:", f"  - {scalar(f'type/{item.type}')}", f"  - {scalar(f'status/{item.status}')}"]
    lines.append("---")
    return "\n".join(lines)


def wikilink(line: str, own: str, names: dict[str, str]) -> str:
    """Turn every identifier that names a note in this export into a link to it.

    A bracket pair the tool wrote is prose, not a link — an item that says
    "declare it in [[sources]]" means the TOML table — so it is escaped first.
    A note never links to itself. A clause link shows the identifier the tool
    wrote as its text.
    """
    line = line.replace("[[", "\\[\\[").replace("]]", "\\]\\]")

    def link(match: re.Match[str]) -> str:
        identifier = match.group(0)
        name = names.get(identifier)
        if name is None or identifier == own:
            return identifier
        return f"[[{identifier}]]" if name == identifier else f"[[{name}|{identifier}]]"

    return IDENTIFIER.sub(link, line)


def _link(identifier: str, names: dict[str, str]) -> str:
    name = names[identifier]
    return f"[[{identifier}]]" if name == identifier else f"[[{name}|{identifier}]]"


def _label(link_type: str) -> str:
    """The tool's own label for a link type — ``derives_from`` -> ``Derives from``."""
    return link_type.replace("_", " ").capitalize()


def note_body(block: NoteBlock, graph: Graph, names: dict[str, str]) -> list[str]:
    """The tool's block reshaped for a note (SR-0009).

    The item line becomes a level-one heading with the type and status on the
    line beneath; the words, rationale and outgoing link lines follow as the
    tool wrote them, wikilinked; the attribute line goes, because the front
    matter already carries every attribute; then one line per incoming link
    type names what links to this item, worded as the link type reads with
    the word "this", so a reader of a requirement sees what rests on it.
    """
    head = ITEM_LINE.match(block.lines[0])
    assert head is not None
    identifier, reference, title, type_, status = head.groups()
    # The heading goes through the same link pass as any line: a title that
    # names another item links to it, and a bracket pair in a title is prose.
    lines = [
        wikilink(f"# {identifier}{f' ({reference})' if reference else ''} — {title}", block.id, names),
        f"{type_.replace('_', ' ')} · {status}",
    ]
    for line in block.lines[1:]:
        if ATTRS_LINE.match(line):
            continue
        lines.append(wikilink(line, block.id, names))
    while lines and not lines[-1]:
        lines.pop()

    by_type: dict[str, list[str]] = {}
    for source, link_type in graph.incoming.get(block.id, []):
        if source in names:
            by_type.setdefault(link_type, []).append(source)
    if by_type:
        lines.append("")
        for link_type in sorted(by_type):
            sources = ", ".join(_link(uid, names) for uid in sorted(by_type[link_type]))
            lines.append(f"*{_label(link_type)} this:* {sources}")
    return lines


def to_notes(markdown: str, graph: Graph, provenance: Provenance, folder: str = "") -> list[Entry]:
    """The notes, as the files of the folder. ``folder`` prefixes every path when set."""
    blocks = blocks_of(markdown)
    registers = {r.prefix: r.title for r in graph.registers}
    names = {block.id: note_name(block.id) for block in blocks}
    prefix = f"{folder}/" if folder else ""

    entries: list[Entry] = []
    for block in blocks:
        item = graph.borrowed.get(block.id) if block.borrowed else graph.items.get(block.id)
        if item is None:
            # Two readings of one graph disagree; an export that quietly
            # dropped the block would hide it.
            raise ValueError(f"the tool wrote {block.id}, which is not in the graph's export")
        head = ITEM_LINE.match(block.lines[0])
        reference = head.group(2) if head else None
        body = "\n".join(note_body(block, graph, names))
        entries.append(
            (
                f"{prefix}{_folder_of(block, registers)}/{note_name(block.id)}.md",
                utf8(f"{front_matter(item, block.id, reference)}\n{body}\n"),
            )
        )
    entries.append((f"{prefix}About this export.md", utf8(_about(provenance, blocks))))
    return entries


def _about(p: Provenance, blocks: list[NoteBlock]) -> str:
    items = sum(1 for b in blocks if not b.borrowed)
    clauses = len(blocks) - items
    plural = lambda n, word: f"{n} {word}{'' if n == 1 else 's'}"  # noqa: E731
    held = f"This export holds {plural(items, 'item')}"
    held += (
        f" and {plural(clauses, 'cited clause')} of adopted sources, under `sources`."
        if clauses
        else "."
    )
    return "\n".join(
        [
            "---",
            f"repository: {scalar(p.repository)}",
            f"ref: {scalar(p.ref or None)}",
            f"commit: {scalar(p.commit or None)}",
            f"working_tree: {scalar(p.tree)}",
            f"produced_by: {scalar(p.tool)}",
            "---",
            f"# {p.repository} — requirements",
            "",
            *[f"- {line}" for line in p.lines()],
            "",
            "Open this folder as a vault. Each note is one item of the intent graph, in a "
            "folder named for its register, and every link between items is a link between "
            "notes. The graph view draws the whole intent graph from them; a note's backlinks "
            "list what rests on it. Type and status are tags, so the graph can be filtered by "
            "either.",
            "",
            held,
            "",
            "The words of every note are the ones the tool publishes; this folder is a record "
            "of the graph as it stood, not a copy to edit.",
            "",
        ]
    )
