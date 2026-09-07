# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""A print-ready HTML document (SR-0008).

One self-contained file: a title page, a contents list, a section per register,
a heading per item, and the cited clauses as appendices, with the print
typography embedded and A4 page rules for the browser that prints it. There is
no PDF writer here and that is the decision rather than a gap — every browser
prints to PDF with a renderer that is already on the machine.

Every string reaches the page through ``html.escape``. Nothing in an item's
text can become markup.
"""

from __future__ import annotations

from html import escape

from .blocks import Block
from .provenance import Provenance

_STYLE = """
:root { color-scheme: light; }
body { margin: 0; background: #f4f4f4; color: #000; font-family: Georgia, "Times New Roman", serif; }
article { max-width: 190mm; margin: 0 auto; padding: 24mm 20mm; background: #fff; font-size: 10.5pt; line-height: 1.45; }
h1 { font-size: 26pt; line-height: 1.2; margin: 0 0 1.2em; }
.front { min-height: 120mm; padding-top: 60mm; }
.front p { font-size: 11pt; margin: 0.2em 0; color: #333; }
h2 { font-size: 18pt; margin: 0 0 0.8em; padding-bottom: 0.25em; border-bottom: 1.5pt solid #000; }
h3 { font-size: 14pt; margin: 1.4em 0 0.6em; }
h4 { font-size: 11.5pt; margin: 1.1em 0 0.15em; }
section.part { margin-top: 2em; }
section.item { margin-bottom: 0.6em; }
.meta { font-size: 9pt; color: #444; margin: 0 0 0.4em; }
p, blockquote { margin: 0.35em 0; }
blockquote { margin: 0.4em 0 0.4em 1.5em; font-style: italic; }
.attrs { font-size: 8.5pt; color: #555; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 0.6em 0; }
th, td { border: 0.5pt solid #888; padding: 0.25em 0.4em; text-align: left; vertical-align: top; }
th { background: #eee; }
nav.contents ol { list-style: none; padding-left: 0; margin: 0; }
nav.contents ol ol { padding-left: 1.4em; font-size: 9.5pt; }
nav.contents li { margin: 0.12em 0; }
nav.contents a { color: #000; text-decoration: none; }
@media print {
  @page { size: A4; margin: 22mm 20mm 24mm; }
  body { background: #fff; }
  article { max-width: none; margin: 0; padding: 0; }
  .front { break-after: page; }
  nav.contents { break-after: page; }
  section.part { break-before: page; margin-top: 0; }
  h2, h3, h4 { break-after: avoid; }
  section.item { break-inside: avoid; }
  thead { display: table-header-group; }
  tr { break-inside: avoid; }
}
"""


def _beneath(block: Block) -> str | None:
    if block.item:
        return f"{block.item['type'].replace('_', ' ')} · {block.item['status']}"
    return block.subtitle


def to_html(blocks: list[Block], provenance: Provenance) -> str:
    title = next((b.text for b in blocks if b.heading == 1), f"{provenance.repository} — requirements")

    body: list[str] = []
    contents: list[str] = []
    depth = 0
    headings = 0
    open_part = False
    open_item = False

    def close_item() -> None:
        nonlocal open_item
        if open_item:
            body.append("</section>")
            open_item = False

    def close_part() -> None:
        nonlocal open_part
        close_item()
        if open_part:
            body.append("</section>")
            open_part = False

    def entry(level: int, anchor: str, text: str) -> None:
        nonlocal depth
        # Levels 2–4 become nesting depths 1–3 in the contents list.
        wanted = level - 1
        while depth < wanted:
            contents.append("<ol>")
            depth += 1
        while depth > wanted:
            contents.append("</ol>")
            depth -= 1
        contents.append(f'<li><a href="#{anchor}">{escape(text)}</a></li>')

    front: list[str] = []
    for block in blocks:
        if block.table:
            head = "".join(f"<th>{escape(c)}</th>" for c in block.table["header"])
            rows = "".join(
                "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in row) + "</tr>" for row in block.table["rows"]
            )
            body.append(f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
            continue
        if block.heading == 1:
            front.append(f"<h1>{escape(block.text)}</h1>")
            continue
        if block.front:
            front.append(f"<p>{escape(block.text)}</p>")
            continue
        if block.heading:
            headings += 1
            anchor = f"h-{headings}"
            level = min(block.heading, 6)
            if block.heading == 2:
                close_part()
                body.append('<section class="part">')
                open_part = True
            elif block.item:
                close_item()
                body.append('<section class="item">')
                open_item = True
            else:
                close_item()
            body.append(f'<h{level} id="{anchor}">{escape(block.text)}</h{level}>')
            beneath = _beneath(block)
            if beneath:
                body.append(f'<p class="meta">{escape(beneath)}</p>')
            if block.heading <= 4:
                entry(block.heading, anchor, block.text)
            continue
        if block.quote:
            body.append(f"<blockquote>{escape(block.text)}</blockquote>")
        elif block.small:
            body.append(f'<p class="attrs">{escape(block.text)}</p>')
        else:
            body.append(f"<p>{escape(block.text)}</p>")
    close_part()
    while depth > 0:
        contents.append("</ol>")
        depth -= 1

    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(title)}</title>\n<style>{_STYLE}</style>\n</head>\n<body>\n<article>\n"
        '<header class="front">\n' + "\n".join(front) + "\n</header>\n"
        '<nav class="contents">\n<h2>Contents</h2>\n' + "\n".join(contents) + "\n</nav>\n"
        + "\n".join(body)
        + "\n</article>\n</body>\n</html>\n"
    )
