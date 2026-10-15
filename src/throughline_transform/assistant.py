# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The graph handed to an assistant that reads a few files and cannot run tl
(UR-0008, SR-0017, SR-0018).

Such an assistant — Microsoft 365 Copilot in a controlled environment reads at
most fifty files, runs no command and returns only text — has to read the whole
graph from a handful of files and be told, in those files, how to send changes
back. This form is a folder: one file per register, each carrying that
register's items exactly as ``tl dump`` gives them, fingerprint included, and a
manifest that says what the export was true of, which file holds which
register, which tl wrote it, and the change-set form ``tl apply`` accepts —
taken from the tool, never written here, so it cannot drift from what apply
reads. One file per register because the assistant's cap counts files, not
items; a folder rather than an archive because an assistant cannot open one.

Nothing of an item is reshaped or computed here (NG-0001): the words and the
fingerprint are the dump's. What this module adds is the file boundaries, the
wrapping, and the manifest.
"""

from __future__ import annotations

import json
from typing import Any

from .model import prefix_of
from .package import Entry, utf8
from .provenance import Provenance

#: How each file is written: JSON, or Markdown holding one fenced JSON block for
#: an assistant that will not read a ``.json`` file.
WRAPS = ("json", "md")

#: The version of this form, stated in the manifest.
FORM_VERSION = 1

MANIFEST = "manifest"

#: What the manifest tells the assistant to do, beside the form it must write.
INSTRUCTION = (
    "Read every file named under \"files\" before you answer — each has the same "
    "extension as this manifest: together they are the whole graph as it stood at "
    "the commit named under \"provenance\". Send changes "
    "back as one change set in the form given under \"change_set_format\", quoting "
    "each item's \"fingerprint\" exactly as these files give it. Never send a "
    "rewritten item file, and never a file at all: a change set is text, and the "
    "person who gave you this folder will apply it."
)


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _entry(name: str, title: str, data: dict[str, Any], wrap: str, after: str = "") -> Entry:
    """One file of the folder: the JSON itself, or Markdown holding it in one
    fenced block, with ``after`` — Markdown of its own — following the block."""
    text = _json(data)
    if wrap == "json":
        return (f"{name}.json", utf8(text))
    body = f"# {title}\n\n```json\n{text}```\n"
    if after:
        body += f"\n{after}"
    return (f"{name}.md", utf8(body))


def to_assistant(
    dump: dict[str, Any],
    provenance: Provenance,
    change_set_format: str,
    *,
    wrap: str = "json",
    only: tuple[str, ...] = (),
) -> list[Entry]:
    """The folder's files, the manifest first.

    ``dump`` is ``tl dump``'s document, unreshaped; ``change_set_format`` is what
    ``tl apply --describe`` printed. With ``only``, the register files hold the
    items named and the clauses they cite, and the manifest says how many of how
    many, as every narrowed output does (SR-0016).
    """
    if wrap not in WRAPS:
        raise ValueError(f"wrap must be one of {', '.join(WRAPS)}, not {wrap!r}")
    items: list[dict[str, Any]] = list(dump.get("items") or [])
    if only:
        keep = set(only)
        own = [i for i in items if not i.get("source") and i["uid"] in keep]
        cited = {link["target"] for i in own for link in i.get("links") or []}
        items = own + [i for i in items if i.get("source") and i["uid"] in cited]
    registers: list[dict[str, Any]] = list(dump.get("registers") or [])
    by_register: dict[str, list[dict[str, Any]]] = {r["prefix"]: [] for r in registers}
    borrowed: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        if item.get("source"):
            borrowed.setdefault(str(item["source"]), []).append(item)
        else:
            by_register.setdefault(prefix_of(item["uid"]), []).append(item)

    files: list[dict[str, Any]] = []
    entries: list[Entry] = []
    for register in registers:
        prefix = register["prefix"]
        title = register.get("title") or prefix
        held = by_register.get(prefix, [])
        entries.append(_entry(prefix, f"{title} ({prefix})", {"register": register, "items": held}, wrap))
        files.append({"file": prefix, "register": prefix, "title": title, "items": len(held)})
    for namespace, clauses in sorted(borrowed.items()):
        name = f"source-{namespace}"
        entries.append(
            _entry(name, f"Clauses of the adopted source {namespace}", {"source": namespace, "items": clauses}, wrap)
        )
        files.append({"file": name, "source": namespace, "items": len(clauses)})

    meta = dump.get("throughline_dump") or {}
    # The manifest is the same in either wrapping, so a file is named by its stem:
    # the reader holds the files, and sees their kind.
    manifest: dict[str, Any] = {
        "throughline_assistant_form": FORM_VERSION,
        "provenance": provenance.record(),
        "provenance_lines": provenance.lines(),
        "tl": str(meta.get("tool_version") or "?"),
        "dump_schema_version": meta.get("dump_schema_version"),
        "files": files,
        "config": dump.get("config") or {},
    }
    if dump.get("composition"):
        manifest["composition"] = dump["composition"]
    manifest["instruction"] = INSTRUCTION
    manifest["change_set_format"] = change_set_format
    readable = f"## How to answer\n\n{INSTRUCTION}\n\n{change_set_format}" if wrap == "md" else ""
    entries.insert(0, _entry(MANIFEST, "Manifest", manifest, wrap, readable))
    return entries
