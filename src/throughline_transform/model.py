# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The graph as ``tl dump`` exports it (throughline SR-0055).

These types describe the tool's own output; nothing here re-derives anything
about the graph. The one thing computed locally is the reverse link index, which
is not a rule — it is the same edges read the other way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Link:
    target: str
    type: str
    stamp: str | None = None


@dataclass
class Item:
    uid: str
    type: str
    status: str
    title: str
    text: str | None = None
    rationale: str | None = None
    normative: bool | None = None
    links: list[Link] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)
    #: The namespace a borrowed item came from, as ``tl-compose dump`` states it.
    #: ``None`` on the graph's own items.
    source: str | None = None


@dataclass(frozen=True)
class Register:
    prefix: str
    digits: int
    title: str
    item_count: int


@dataclass(frozen=True)
class Source:
    namespace: str
    url: str | None = None
    ref: str | None = None
    subdir: str | None = None
    path: str | None = None
    item_count: int | None = None


@dataclass
class Graph:
    #: The graph's own items, by UID. Never a borrowed one.
    items: dict[str, Item]
    #: UID -> (from, link type) for every edge pointing at it.
    incoming: dict[str, list[tuple[str, str]]]
    #: Register prefix -> its items, in UID order.
    by_register: dict[str, list[Item]]
    registers: list[Register]
    config: dict[str, Any]
    #: The clauses of every adopted source, by namespace-qualified identifier.
    borrowed: dict[str, Item]
    #: The sources the union was assembled from, in the composer's order.
    sources: list[Source]
    #: What the tool called itself in the dump.
    tool_version: str
    composed: bool


def prefix_of(uid: str) -> str:
    """A UID's register prefix — the part before the number."""
    dash = uid.rfind("-")
    return uid if dash == -1 else uid[:dash]


def is_borrowed(target: str) -> bool:
    """A namespace-qualified target names a clause in an adopted source."""
    return ":" in target


def split_borrowed(target: str) -> tuple[str, str]:
    """``asvs:SR-0003`` -> ``("asvs", "SR-0003")``."""
    colon = target.index(":")
    return target[:colon], target[colon + 1 :]


def _item(raw: dict[str, Any]) -> Item:
    return Item(
        uid=raw["uid"],
        type=raw["type"],
        status=raw["status"],
        title=raw.get("title") or "",
        text=raw.get("text"),
        rationale=raw.get("rationale"),
        normative=raw.get("normative"),
        links=[Link(link["target"], link["type"], link.get("stamp")) for link in raw.get("links") or []],
        attrs=dict(raw.get("attrs") or {}),
        source=raw.get("source"),
    )


def index(dump: dict[str, Any], composed: bool) -> Graph:
    """Read the tool's export into the shape the writers need."""
    items: dict[str, Item] = {}
    borrowed: dict[str, Item] = {}
    incoming: dict[str, list[tuple[str, str]]] = {}
    for raw in dump.get("items") or []:
        item = _item(raw)
        (borrowed if item.source else items)[item.uid] = item
    for item in items.values():
        for link in item.links:
            incoming.setdefault(link.target, []).append((item.uid, link.type))

    registers = [
        Register(r["prefix"], int(r.get("digits", 4)), r.get("title") or r["prefix"], int(r.get("item_count", 0)))
        for r in dump.get("registers") or []
    ]
    by_register: dict[str, list[Item]] = {r.prefix: [] for r in registers}
    for item in items.values():
        by_register.setdefault(prefix_of(item.uid), []).append(item)

    composition = dump.get("composition") or {}
    sources = [
        Source(
            namespace=s["namespace"],
            url=s.get("url"),
            ref=s.get("ref"),
            subdir=s.get("subdir"),
            path=s.get("path"),
            item_count=s.get("item_count"),
        )
        for s in composition.get("sources") or []
    ]
    meta = dump.get("throughline_dump") or {}
    return Graph(
        items=items,
        incoming=incoming,
        by_register=by_register,
        registers=registers,
        config=dump.get("config") or {},
        borrowed=borrowed,
        sources=sources,
        tool_version=str(meta.get("tool_version") or "?"),
        composed=composed,
    )


def ground_links(graph: Graph) -> list[str]:
    """The link types that ground an item, as the graph declares them — one matrix each."""
    declared = (graph.config.get("grounding") or {}).get("ground_link_types") or []
    return list(declared) or ["implements"]


def register_titles(graph: Graph) -> dict[str, str]:
    """Register prefix -> title, for the sections a document groups items under."""
    return {r.prefix: r.title for r in graph.registers}


def source_titles(graph: Graph) -> dict[str, str]:
    """Namespace -> where the source comes from, for an appendix's subtitle."""
    out: dict[str, str] = {}
    for s in graph.sources:
        parts = [s.url or s.path or "", f"at {s.ref}" if s.ref else "", f"in {s.subdir}/" if s.subdir else ""]
        out[s.namespace] = " ".join(p for p in parts if p)
    return out
