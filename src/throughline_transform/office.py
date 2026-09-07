# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""xlsx and docx, written from their own specifications (SR-0010).

Both are zips of XML, and both are written here rather than depended on. What
is produced is deliberately plain — a sheet of cells, a document of headings
and paragraphs. Neither format is exercised beyond what a reader needs to sort
a column or read a requirement.
"""

from __future__ import annotations

import re

from .blocks import Block
from .package import Entry, archive, utf8, xml
from .tables import Table

# --- xlsx ------------------------------------------------------------------


def column_name(index: int) -> str:
    """Column names in a sheet — A, B, … Z, AA, AB, …"""
    name = ""
    n = index + 1
    while n > 0:
        remainder = (n - 1) % 26
        name = chr(65 + remainder) + name
        n = (n - remainder) // 26
    return name


def _widths(table: Table) -> list[int]:
    """Column widths from the content, bounded at both ends."""
    widths = []
    for i, name in enumerate(table.columns):
        longest = max([len(name), *[len(row[i]) if i < len(row) else 0 for row in table.rows]])
        widths.append(min(60, max(10, longest + 2)))
    return widths


def _sheet_xml(table: Table) -> str:
    def row(cells: list[str], index: int) -> str:
        style = 1 if index == 0 else 2
        out = [f'<row r="{index + 1}">']
        for column, value in enumerate(cells):
            out.append(
                f'<c r="{column_name(column)}{index + 1}" t="inlineStr" s="{style}">'
                f'<is><t xml:space="preserve">{xml(value)}</t></is></c>'
            )
        out.append("</row>")
        return "".join(out)

    last = f"{column_name(max(0, len(table.columns) - 1))}{len(table.rows) + 1}"
    cols = "".join(
        f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(_widths(table))
    )
    data = "".join(row(cells, i) for i, cells in enumerate([table.columns, *table.rows]))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        # The header row is frozen: a table of requirements is longer than a
        # screen, and a column nobody can name is not sortable.
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<cols>{cols}</cols>"
        f"<sheetData>{data}</sheetData>"
        # Read-only, without a password (SR-0007): a guard against a stray
        # keystroke and a statement that this is a record. Sorting, filtering
        # and selecting stay permitted. In this element a 0 means "allowed".
        '<sheetProtection sheet="1" objects="1" scenarios="1" '
        'selectLockedCells="0" selectUnlockedCells="0" sort="0" autoFilter="0"/>'
        f'<autoFilter ref="A1:{last}"/>'
        "</worksheet>"
    )


def sheet_name(name: str, index: int) -> str:
    """A sheet name Excel will accept: 31 characters, and none of \\/?*[]:"""
    clean = re.sub(r"[\\/?*\[\]:]", " ", name).strip()[:31]
    return clean or f"Sheet{index + 1}"


def to_xlsx(tables: list[Table]) -> bytes:
    names = [sheet_name(t.name, i) for i, t in enumerate(tables)]
    n = len(tables)
    entries: list[Entry] = [
        (
            "[Content_Types].xml",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                + "".join(
                    f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
                    'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                    for i in range(n)
                )
                + "</Types>"
            ),
        ),
        (
            "_rels/.rels",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                "</Relationships>"
            ),
        ),
        (
            "xl/workbook.xml",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                # Opened read-only by recommendation, structure locked so no
                # sheet is added, removed or renamed (SR-0007).
                '<fileSharing readOnlyRecommended="1"/>'
                '<workbookProtection lockStructure="1"/>'
                "<sheets>"
                + "".join(
                    f'<sheet name="{xml(name)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, name in enumerate(names)
                )
                + "</sheets></workbook>"
            ),
        ),
        (
            "xl/_rels/workbook.xml.rels",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + "".join(
                    f'<Relationship Id="rId{i + 1}" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                    f'Target="worksheets/sheet{i + 1}.xml"/>'
                    for i in range(n)
                )
                + f'<Relationship Id="rId{n + 1}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                'Target="styles.xml"/>'
                "</Relationships>"
            ),
        ),
        (
            "xl/styles.xml",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
                '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
                # A fill and a border are required even when nothing uses them —
                # Excel indexes into these tables and refuses a file whose
                # counts do not line up.
                '<fills count="2"><fill><patternFill patternType="none"/></fill>'
                '<fill><patternFill patternType="gray125"/></fill></fills>'
                '<borders count="1"><border/></borders>'
                '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
                '<cellXfs count="3">'
                '<xf xfId="0"/>'
                '<xf xfId="0" fontId="1" applyFont="1" applyAlignment="1">'
                '<alignment vertical="top" wrapText="1"/></xf>'
                '<xf xfId="0" applyAlignment="1">'
                '<alignment vertical="top" wrapText="1"/></xf>'
                "</cellXfs>"
                '<cellStyles count="1">'
                '<cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
                "</styleSheet>"
            ),
        ),
        *[(f"xl/worksheets/sheet{i + 1}.xml", utf8(_sheet_xml(t))) for i, t in enumerate(tables)],
    ]
    return archive(entries)


# --- docx ------------------------------------------------------------------


def _run(text: str, bold: bool = False) -> str:
    lines = "".join(
        ("" if i == 0 else "<w:br/>") + f'<w:t xml:space="preserve">{xml(line)}</w:t>'
        for i, line in enumerate(text.split("\n"))
    )
    return f"<w:r>{'<w:rPr><w:b/></w:rPr>' if bold else ''}{lines}</w:r>"


def _table_xml(header: list[str], rows: list[list[str]]) -> str:
    def side(edge: str) -> str:
        return f'<w:{edge} w:val="single" w:sz="4" w:space="0" w:color="auto"/>'

    def tc(text: str, bold: bool) -> str:
        return (
            '<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>'
            f"<w:p>{_run(text, bold)}</w:p></w:tc>"
        )

    def tr(cells: list[str], head: bool) -> str:
        return (
            f"<w:tr>{'<w:trPr><w:tblHeader/></w:trPr>' if head else ''}"
            + "".join(tc(c, head) for c in cells)
            + "</w:tr>"
        )

    width = 9360 // max(1, len(header))
    return (
        '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>'
        + "".join(side(e) for e in ["top", "left", "bottom", "right", "insideH", "insideV"])
        + "</w:tblBorders></w:tblPr>"
        # The grid is required, not decorative: a table without it is one Word
        # will usually render and a conforming reader refuses outright.
        "<w:tblGrid>"
        + "".join(f'<w:gridCol w:w="{width}"/>' for _ in header)
        + "</w:tblGrid>"
        + tr(header, True)
        + "".join(tr(r, False) for r in rows)
        + "</w:tbl>"
    )


def _paragraph(block: Block) -> str:
    if block.table:
        return _table_xml(block.table["header"], block.table["rows"])
    if block.heading:
        style = f'<w:pStyle w:val="Heading{min(block.heading, 4)}"/>'
    elif block.quote:
        style = '<w:pStyle w:val="Quote"/>'
    elif block.small:
        style = '<w:pStyle w:val="Attrs"/>'
    else:
        style = ""
    text = f"<w:p>{f'<w:pPr>{style}</w:pPr>' if style else ''}{_run(block.text)}</w:p>"
    beneath = (
        f"{block.item['type'].replace('_', ' ')} · {block.item['status']}" if block.item else block.subtitle
    )
    if beneath:
        text += f'<w:p><w:pPr><w:pStyle w:val="Attrs"/></w:pPr>{_run(beneath)}</w:p>'
    return text


def _contents_xml() -> str:
    """A table of contents Word fills in when asked (SR-0008)."""
    return (
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>' + _run("Contents") + "</w:p>"
        '<w:p><w:fldSimple w:instr="TOC \\o &quot;1-4&quot; \\h \\z \\u">'
        + _run("Right-click here and choose Update Field to fill in the contents.")
        + "</w:fldSimple></w:p>"
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    )


_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
    '<w:sz w:val="22"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults>'
    + "".join(
        f'<w:style w:type="paragraph" w:styleId="Heading{level}">'
        f'<w:name w:val="heading {level}"/><w:basedOn w:val="Normal"/>'
        f'<w:pPr><w:outlineLvl w:val="{level - 1}"/><w:spacing w:before="240"/></w:pPr>'
        f'<w:rPr><w:b/><w:sz w:val="{36 - level * 4}"/></w:rPr></w:style>'
        for level in (1, 2, 3, 4)
    )
    + '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/>'
    '<w:pPr><w:ind w:left="720"/></w:pPr><w:rPr><w:i/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Attrs"><w:name w:val="Attrs"/>'
    '<w:basedOn w:val="Normal"/><w:rPr><w:sz w:val="18"/><w:color w:val="555555"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/></w:style>'
    "</w:styles>"
)


def to_docx(blocks: list[Block]) -> bytes:
    first_section = next((i for i, b in enumerate(blocks) if b.heading == 2), -1)
    body: list[str] = []
    for i, block in enumerate(blocks):
        if i == first_section:
            body.append(_contents_xml())
        elif block.heading == 2:
            body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        body.append(_paragraph(block))
        # Word joins two tables that touch into one.
        if block.table and i + 1 < len(blocks) and blocks[i + 1].table:
            body.append("<w:p/>")
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(body) +
        # A4, with a margin on every side.
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1418" w:right="1134" w:bottom="1418" w:left="1134" w:header="709" w:footer="709"/>'
        "</w:sectPr>"
        "</w:body></w:document>"
    )
    entries: list[Entry] = [
        (
            "[Content_Types].xml",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                "</Types>"
            ),
        ),
        (
            "_rels/.rels",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                "</Relationships>"
            ),
        ),
        (
            "word/_rels/document.xml.rels",
            utf8(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                "</Relationships>"
            ),
        ),
        ("word/styles.xml", utf8(_STYLES)),
        ("word/document.xml", utf8(document)),
    ]
    return archive(entries)
