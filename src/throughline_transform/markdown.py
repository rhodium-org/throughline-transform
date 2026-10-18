# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The Markdown document, written by the tool (SR-0002).

A document of directives and empty regions is handed to the docs command, and
what comes back is what the tool wrote. Which entry point runs is the graph's
decision (SR-0001).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import Graph, ground_links
from .project import docs
from .provenance import Provenance
from .shape import MARKER


@dataclass(frozen=True)
class Options:
    #: Full item blocks, a compact table, or both.
    body: str = "catalog"
    #: A traceability matrix per grounding link type.
    matrix: bool = False
    #: The tool's own summary of the graph's shape.
    stats: bool = True
    #: Keep the tool's region markers, so the document is one ``tl docs`` can refill.
    markers: bool = False
    #: For the tabular outputs: one table for everything, or one per register.
    split: str = "one"
    #: The items the output holds, where the caller named them (SR-0016);
    #: empty for every item.
    only: tuple[str, ...] = ()


def _region(directive: str) -> str:
    return f"<!-- tl:{directive} -->\n<!-- tl:end -->"


def _within(expression: str, opts: Options) -> str:
    """A directive's filter, joined with the items named, so tl docs writes only those (SR-0016).

    The identifiers are ones the graph holds (the command refuses any other), so
    each is written as a quoted literal the filter language reads (tl:SR-0045).
    """
    if not opts.only:
        return expression
    named = ", ".join(repr(uid) for uid in opts.only)
    return f"({expression}) and (uid in [{named}])"


def directive_document(graph: Graph, opts: Options, provenance: Provenance) -> str:
    """The document the tool is asked to fill."""
    lines: list[str] = [f"# {provenance.repository} — requirements", ""]
    lines += [f"- {line}" for line in provenance.lines()]
    lines.append("")

    if opts.stats:
        lines += ["## Summary", "", _region(f"stats {_within('True', opts)}"), ""]
    if opts.body in ("table", "both"):
        lines += ["## Items", "", _region(f"table {_within('True', opts)}"), ""]
    if opts.matrix:
        # One matrix per grounding link type the graph declares, each over the
        # items something actually reaches by that link. Over every item a
        # matrix is mostly a column of dashes.
        lines += ["## Traceability", ""]
        for link_type in ground_links(graph):
            lines += [
                f"### {link_type.replace('_', ' ')}",
                "",
                _region(f"matrix incoming:{link_type} {_within(f'links.incoming({link_type!r})', opts)}"),
                "",
            ]
    if opts.body in ("catalog", "both"):
        lines += ["## Every item", "", _region(f"catalog {_within('True', opts)}"), ""]
    # The words every cited clause answers to. Only over a composed graph: the
    # directive is the composer's, and a graph adopting no source has nothing
    # to mirror.
    if graph.composed:
        lines += ["## Clauses of adopted sources", "", _region(f"sourced {_within('True', opts)}"), ""]
    return "\n".join(lines)


def strip_markers(markdown: str) -> str:
    """Take out the tool's region markers, leaving what it wrote between them."""
    kept = [line for line in markdown.split("\n") if not MARKER.match(line)]
    # A removed marker leaves the blank line that was around it, so runs of
    # three or more collapse to the one a Markdown reader expects.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept))


def to_markdown(root: Path, graph: Graph, opts: Options, provenance: Provenance) -> str:
    written = docs(root, directive_document(graph, opts, provenance), graph.composed)
    return written if opts.markers else strip_markers(written)
