# throughline-transform — specification

<!-- Generated from this repository's own requirements graph. Do not edit the
     blocks between `tl:item` markers by hand — run `tl-compose -C idd docs` and
     they are rewritten from the graph. The headings and the prose between blocks
     are hand-owned and are left alone.

     `tl-compose -C idd docs --check` fails if any block here has fallen behind the
     graph, and `tl-compose -C idd check --strict` fails if a live normative item is
     missing from this document altogether. -->

This document is the whole of what throughline-transform is built to, rendered
from the items under [`idd/`](..). Clauses borrowed from throughline's own graph
are not reproduced here — they belong to that graph and are read there; what
follows is this project's own.

## Summary

<!-- tl:stats True -->
- **Items:** 18 — system_requirement 11 · non_goal 3 · user_requirement 3 · intent 1
- **Links:** 19 — implements 11 · satisfies 5 · derives_from 3
- **Grounding depth:** max 2 · mean 1.4
- **Most connected:** UR-0002 (9) · INT-0001 (3) · SR-0002 (3)
- **Degree distribution:** 0 → 3 · 1 → 7 · 2 → 4 · 3 → 3 · 9 → 1
<!-- tl:end -->


## Intent

Why throughline-transform exists. Everything below grounds upward into this.

<!-- tl:item INT-0001 -->
**INT-0001 — The outputs of a graph come from the graph on disk, committed or not** — `intent`, status `proposed`

> A person with a throughline graph on their own machine can produce every form a reader opens — a document, a spreadsheet, a folder of notes — from the working tree as it is, before anything is committed or pushed, with one command. The output says what state the tree was in.

*Rationale:* The editor produces these outputs from a graph on GitHub. A graph that is not yet committed, or that lives where the editor cannot reach, has no way out. The person who needs the output most often has the graph open on their own disk and wants to see what a reader will see before they commit it.

**origin**: ai
<!-- tl:end -->


## Non-goals

What is deliberately left out, recorded so a reviewer or an agent can point at it.

<!-- tl:item NG-0001 -->
**NG-0001 — No second renderer of an item's words** — `non_goal`, status `proposed`

> This tool never composes the prose of an item. Every word of an item in an output is written by tl docs. The tool adds containers, front matter and link syntax, and nothing else.

*Rationale:* A second renderer drifts from what tl docs --check gates, and a document that quietly differs from the published specification is worse than none.

**origin**: ai
<!-- tl:end -->

<!-- tl:item NG-0002 -->
**NG-0002 — No PDF writer** — `non_goal`, status `proposed`

> This tool ships no PDF renderer. The print-ready HTML output is what a browser prints to PDF.

*Rationale:* A PDF library is the largest dependency this package could take, for a format every browser already produces with a renderer maintained by someone else.

**origin**: ai
<!-- tl:end -->

<!-- tl:item NG-0003 -->
**NG-0003 — No server and no user interface** — `non_goal`, status `proposed`

> This tool is a command run over a directory. It listens on nothing, serves nothing and opens no window.

*Rationale:* The editor is the interactive surface for this family. A second one here would be a second implementation to keep in step.

**origin**: ai
<!-- tl:end -->


## User requirements

What a person with a graph on disk can do.

<!-- tl:item UR-0001 -->
**UR-0001 — Produce an output from a working tree with one command** — `user_requirement`, status `proposed`

> From a directory holding a graph, or from any directory beneath it, one command names a format and writes one file, or one folder when asked. It works on a tree with uncommitted changes and on a directory that is not under version control at all.

*Rationale:* The graph a person is writing is the one they want to see rendered, and it is not yet committed. Requiring a commit first, or a push, puts the check after the decision it should inform.

*Derives from:* INT-0001

**origin**: ai · **verification**: Run the command on a graph with an uncommitted edit and on a copy outside git. Each produces the file, and each output's provenance says which it was.
<!-- tl:end -->

<!-- tl:item UR-0002 -->
**UR-0002 — The same six forms the editor offers** — `user_requirement`, status `proposed`

> Markdown, a folder of notes for a note-taking tool such as Obsidian, CSV, an Excel workbook, a Word document, and a print-ready HTML document. Each holds what the editor's export of the same graph holds: the same items, links, attributes and cited clauses, laid out the same way.

*Rationale:* A reader who was handed a workbook from the editor last week and a workbook from this tool today should not be able to tell which made it. Two shapes for one graph would be two things to explain.

*Derives from:* INT-0001

**origin**: ai · **verification**: For one graph, each output opens in an ordinary reader for that format and lists every item the graph holds. A notes output has one note per item and no wikilink that names no note.
<!-- tl:end -->

<!-- tl:item UR-0003 -->
**UR-0003 — An output says what it was true of** — `user_requirement`, status `proposed`

> Every output names the repository, the ref, the commit and the tool that produced it, and says whether the working tree was clean, had uncommitted changes, or was not under version control.

*Rationale:* An output outlives the tree that made it. An output of an uncommitted graph is useful and must say what it is, because a reader holding the file cannot tell.

*Derives from:* INT-0001

**origin**: ai · **verification**: The provenance lines of an output from a clean tree, a tree with an edit, and a folder outside git read differently, and each is right.
<!-- tl:end -->


## System requirements

How the tool does it. Each implements a user requirement; several read a clause of throughline's own graph, cited as `tl:SR-…`.

<!-- tl:item SR-0001 -->
**SR-0001 — The entry point is decided by the graph, and the tool is run as a command** — `system_requirement`, status `proposed`

> A graph whose configuration declares sources is read through tl-compose; any other through tl. The tool is found beside this package's interpreter first and on the path second, and is run as a command with -C pointing at the graph. Its modules are never imported.

*Rationale:* Over a composed graph the core command exits cleanly and writes a borrowed clause as its synthetic uid alone, dropping the reference number a conformance document exists to carry. The command line is the surface the tool publishes; its modules move between releases, and an import that worked last month is how a sibling package stopped starting.

*Implements:* UR-0002
*Satisfies:* tl:SR-0187

**origin**: ai · **priority**: must · **verification**: On the composed fixture the Markdown carries the borrowed clause as src:SR-0001 and mirrors it. On the plain fixture the core command is run. Removing the tool from the path produces one line saying so.
<!-- tl:end -->

<!-- tl:item SR-0002 -->
**SR-0002 — The Markdown is asked of tl docs over a document of directives** — `system_requirement`, status `proposed`

> The Markdown output is a document of tl directives — a summary, a table of items, one traceability matrix per grounding link type, a catalogue of every item, and the mirrored clauses of adopted sources when the graph composes — handed to the docs command, written outside the graph, and read back. The region markers are stripped unless asked to stay.

*Rationale:* The alternative is rendering items here, which NG-0001 refuses. Written outside the graph so an output can never be mistaken for a change to it.

*Implements:* UR-0002
*Satisfies:* tl:SR-0111, tl:SR-0113

**origin**: ai · **priority**: must · **verification**: The Markdown for the fixture holds the catalogue block of every item, a block this package has no code to produce. With --markers the region markers are present; without, none.
<!-- tl:end -->

<!-- tl:item SR-0003 -->
**SR-0003 — The tool's shape is read in one place** — `system_requirement`, status `proposed`

> The item line, the attribute line and the identifier pattern the tool writes are defined once and read by every writer that cuts or reshapes the tool's Markdown. If the tool changes a line, every output falls back the same way.

*Rationale:* The document formats and the notes both cut the catalogue at the item line. Two definitions of that line is how they would come to disagree about where an item starts.

*Implements:* UR-0002
*Satisfies:* tl:SR-0111

**origin**: ai · **priority**: should · **verification**: One module holds the patterns. A search of the package finds no second definition of the item line.
<!-- tl:end -->

<!-- tl:item SR-0004 -->
**SR-0004 — Provenance is read from git and judged over the graph alone** — `system_requirement`, status `proposed`

> The repository name is read from the origin remote, or failing that the top-level directory's name; the ref from HEAD; the commit from HEAD; and cleanliness from git status over the graph's directory only. Without a repository the tree is reported as not under version control. Without a commit it is reported as holding uncommitted changes.

*Rationale:* Judged over the graph's directory, not the whole repository, because an output is of the graph and a change elsewhere does not alter what it says.

*Implements:* UR-0003

**origin**: ai · **priority**: must · **verification**: A fixture copied into a repository reports clean; after an edit to one item it reports uncommitted changes with the same commit; outside git it reports not under version control with no ref and no commit.
<!-- tl:end -->

<!-- tl:item SR-0005 -->
**SR-0005 — A tabular output is one row per item, over the columns the graph declares** — `system_requirement`, status `proposed`

> csv and xlsx put each item on a row. The columns are the uid, register, type, status, title, text, rationale and normative flag every item has, then each attribute any item in the table carries, then one column per link type listing the targets. The column set is read from the tool's export, never fixed here. One table for everything, or one per register with only the columns its own items use.

*Implements:* UR-0002
*Satisfies:* tl:SR-0055

**origin**: ai · **priority**: must · **verification**: An attribute the package has no knowledge of appears as a populated column. Per register, the Intents table carries no priority column.
<!-- tl:end -->

<!-- tl:item SR-0006 -->
**SR-0006 — A links table names both ends of every link by the sheet each is on** — `system_requirement`, status `proposed`

> Beside the item tables, one table holds one row per link: the sheet and uid it starts from, the link type, and the sheet and uid it points at. A link into an adopted source names the namespace as the sheet. The rows are in item order.

*Rationale:* A reviewer follows what rests on what. A links table can be sorted and filtered by either end; a link listed in a cell cannot.

*Implements:* UR-0002

**origin**: ai · **priority**: must · **verification**: Per register, a relates link between two system requirements names System requirements at both ends; a satisfies link into a source names the namespace.
<!-- tl:end -->

<!-- tl:item SR-0007 -->
**SR-0007 — Cited clauses travel with the export, and the workbook is read-only** — `system_requirement`, status `proposed`

> The clauses of adopted sources that some item links to travel as one table per source, with the columns those clauses carry. The workbook opens read-only by recommendation with its structure locked and no password, and every sheet still sorts and filters. The csv archive says it cannot be protected.

*Rationale:* An export is a record handed to people who did not make it. A copy edited on its way round is no longer a record of anything. csv has no protection, so the archive says so rather than leaving a reader to assume.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: The composed fixture's workbook holds a sheet named by the namespace with exactly the cited clause. The workbook XML carries read-only recommended, structure lock, and sort and filter allowed.
<!-- tl:end -->

<!-- tl:item SR-0008 -->
**SR-0008 — A document output reads as a document** — `system_requirement`, status `proposed`

> The Word and HTML outputs open with a title page naming the provenance, then a contents list, then a section per register with a heading per item carrying its identifier and title, its type and status beneath, its words as a quotation, its rationale, and its attributes in smaller type. Cited clauses follow as one appendix per source with where the source comes from beneath its title. The Word contents is a field Word fills in. The HTML contents is a list of links; page numbers are the browser's to print.

*Rationale:* The structure is read from the shape of the tool's Markdown (SR-0003), never rendered from the graph. Page numbers in HTML would need a paged-media engine no browser ships for print; the browser's own header and footer number the pages.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: The Word document carries Heading2 through Heading4 styles, a TOC field, and a page break per section. The HTML page holds one section per item, a contents list of anchors, and an A4 page rule.
<!-- tl:end -->

<!-- tl:item SR-0009 -->
**SR-0009 — A notes output is one note per item, cut from the catalogue, with wikilinks** — `system_requirement`, status `proposed`

> The catalogue and the mirrored clauses are written once and cut at the item line into one Markdown note per item, in a folder per register named by the register's title; cited clauses go under sources, one folder per namespace, with the colon of the identifier replaced by a space in the file name. Each note opens with YAML front matter holding type, status, normative flag and attributes as properties, the title as an alias, and a tag for the type and one for the status. Every identifier that names a note becomes a wikilink; a clause link shows the identifier the tool wrote as its text. A bracket pair the tool wrote in prose is escaped. An About note carries the provenance.

*Rationale:* The same shape the editor produces, so a vault from either opens the same way. The colon is replaced because a note tool refuses one in a name and links by basename across the whole vault. Brackets in prose are escaped because an item that says declare it in [[sources]] would otherwise draw a ghost note.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: For the fixtures, one note per item under its register's folder, front matter that parses as YAML with the item's properties, every wikilink naming a note in the folder, the TOML brackets escaped, and a clause note named with a space where the colon was.
<!-- tl:end -->

<!-- tl:item SR-0010 -->
**SR-0010 — No dependency beyond the throughline family and the standard library** — `system_requirement`, status `proposed`

> The package depends on throughline and throughline-compose and nothing else. xlsx and docx are written from their own specifications over the standard library's zip module. There is no PDF writer (NG-0002).

*Rationale:* Every dependency is one more thing to audit for a tool people install with pipx to run over their own requirements. The cost of writing two Office formats by hand is a few hundred lines already proven in the editor.

*Implements:* UR-0001

**origin**: ai · **priority**: must · **verification**: The dependency list in pyproject.toml names the two packages only. The Office outputs open in LibreOffice.
<!-- tl:end -->

<!-- tl:item SR-0011 -->
**SR-0011 — One file per run, a folder when asked, the same bytes for the same graph** — `system_requirement`, status `proposed`

> Every format writes one file. The notes and csv outputs are a zip by default, or the files written into a folder with --folder. When no name is given one is chosen from the provenance. Zip timestamps are fixed at the format's epoch, so the same graph exported twice gives identical bytes. A path that would escape the folder is refused. A wrong directory, a tool that refuses, or a file that cannot be written is one line on stderr and exit code 1; a usage error is exit code 2.

*Rationale:* An output that differs only in when it was taken cannot be compared with the one before it, and comparing them is what people do with a specification.

*Implements:* UR-0001

**origin**: ai · **priority**: should · **verification**: Each format writes a file that opens; --folder unpacks the vault; two runs over one graph are byte-identical; a directory without a graph gives one line on stderr and exit 1; --folder on xlsx exits 2.
<!-- tl:end -->


## Traceability

### implements

<!-- tl:matrix incoming:implements links.incoming('implements') -->
| UID | Title | Implements (incoming) |
|---|---|---|
| UR-0001 | Produce an output from a working tree with one command | SR-0010, SR-0011 |
| UR-0002 | The same six forms the editor offers | SR-0001, SR-0002, SR-0003, SR-0005, SR-0006, SR-0007, SR-0008, SR-0009 |
| UR-0003 | An output says what it was true of | SR-0004 |
<!-- tl:end -->

### derives from

<!-- tl:matrix incoming:derives_from links.incoming('derives_from') -->
| UID | Title | Derives_from (incoming) |
|---|---|---|
| INT-0001 | The outputs of a graph come from the graph on disk, committed or not | UR-0001, UR-0002, UR-0003 |
<!-- tl:end -->
