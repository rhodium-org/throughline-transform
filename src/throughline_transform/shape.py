# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""The shape of what the tool writes, read in one place (SR-0003).

``tl docs`` renders an item as a bold line, its words as a quotation, its
rationale, one line per link type and a line of attributes (throughline
SR-0111, SR-0113, SR-0187). Nothing here is restated — these patterns are read,
never written. If the tool changes the line, every consumer of this module
falls back the same way rather than each guessing differently.
"""

from __future__ import annotations

import re

#: The line the tool writes to open an item in a catalogue or a mirrored source:
#: ``**UID — title** — `type`, status `status```, where a borrowed clause's UID is
#: namespace-qualified and may carry its reference in brackets.
ITEM_LINE = re.compile(
    r"^\*\*((?:[a-z][a-z0-9_-]*:)?[A-Z][A-Z0-9]*-\d+)(?: \((.*?)\))? — (.+?)\*\* — "
    r"`([^`]+)`, status `([^`]+)`$"
)

#: The tool's attribute line: ``**name**: value · **name**: value``.
ATTRS_LINE = re.compile(r"^\*\*[a-z_]+\*\*: .*$")

#: An identifier as the tool writes one anywhere in prose: a local UID, or a
#: namespace-qualified one naming a clause of an adopted source.
IDENTIFIER = re.compile(r"(?:[a-z][a-z0-9_-]*:)?[A-Z][A-Z0-9]*-\d+")

#: A region marker, opening or closing.
MARKER = re.compile(r"^\s*<!--\s*tl:(?:[a-z.]+|end)\b.*-->\s*$", re.IGNORECASE)
