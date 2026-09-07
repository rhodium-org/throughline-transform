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
- **Items:** 25 — system_requirement 14 · user_requirement 6 · non_goal 3 · intent 2
- **Links:** 28 — implements 14 · derives_from 6 · satisfies 5 · refines 2 · relates 1
- **Grounding depth:** max 2 · mean 1.4
- **Most connected:** UR-0002 (9) · INT-0001 (3) · INT-0002 (3)
- **Degree distribution:** 0 → 3 · 1 → 5 · 2 → 11 · 3 → 5 · 9 → 1
<!-- tl:end -->


## Intent

Why throughline-transform exists. Everything below grounds upward into this.

<!-- tl:item INT-0001 -->
**INT-0001 — The outputs of a graph come from the graph on disk, committed or not** — `intent`, status `ratified`

> A person with a throughline graph on their own machine can produce every form a reader opens — a document, a spreadsheet, a folder of notes — from the working tree as it is, before anything is committed or pushed, with one command. The output says what state the tree was in.

*Rationale:* The editor produces these outputs from a graph on GitHub. A graph that is not yet committed, or that lives where the editor cannot reach, has no way out. The person who needs the output most often has the graph open on their own disk and wants to see what a reader will see before they commit it.

**origin**: ai · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:5c8c4b4356e989b22048214676015a60315e57254b6ebf8bb963d7948a4ea541
<!-- tl:end -->

<!-- tl:item INT-0002 -->
**INT-0002 — One implementation of every form, for the command line and the editor alike** — `intent`, status `ratified`

> The forms a graph leaves in — a document, a workbook, a folder of notes — are produced by one implementation, whichever surface asks for them. The throughline editor runs this package as a wheel under Pyodide, so an export from a browser tab and an export from a terminal are the same bytes for the same graph.

*Rationale:* Before this package existed the editor held its own writers in TypeScript and this package ported them to Python, so there were two implementations of every form and a change to one had to be made in the other or they drifted. The editor already runs tl and tl-compose as unmodified wheels; running this package the same way ends the duplication.

**origin**: ai · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:fd7fc42054311923a5d6946802b3e788ca4839e1ade4e1feb13485f66f7a0ba1
<!-- tl:end -->



## Non-goals

What is deliberately left out, recorded so a reviewer or an agent can point at it.

<!-- tl:item NG-0001 -->
**NG-0001 — No second renderer of an item's words** — `non_goal`, status `ratified`

> This tool never composes the prose of an item. Every word of an item in an output is written by tl docs. The tool adds containers, front matter and link syntax, and nothing else.

*Rationale:* A second renderer drifts from what tl docs --check gates, and a document that quietly differs from the published specification is worse than none.

**origin**: ai · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:f5c33390e2febaec19e6d13dba176393393481e4f256b9d023c921dd8bd9ab41
<!-- tl:end -->

<!-- tl:item NG-0002 -->
**NG-0002 — No PDF writer** — `non_goal`, status `ratified`

> This tool ships no PDF renderer. The print-ready HTML output is what a browser prints to PDF.

*Rationale:* A PDF library is the largest dependency this package could take, for a format every browser already produces with a renderer maintained by someone else.

**origin**: ai · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:d94996ab16dfb87585262313cfd3acd1cada6b19c9d2a38abd4bdc9b655c7bfe
<!-- tl:end -->

<!-- tl:item NG-0003 -->
**NG-0003 — No server and no user interface** — `non_goal`, status `ratified`

> This tool is a command run over a directory. It listens on nothing, serves nothing and opens no window.

*Rationale:* The editor is the interactive surface for this family. A second one here would be a second implementation to keep in step.

**origin**: ai · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:a162c86b2df6460a5be7c61c68d3eb7694a4cb46c3d8fb4aae660cca4c0e9dfe
<!-- tl:end -->


## User requirements

What a person with a graph on disk can do.

<!-- tl:item UR-0001 -->
**UR-0001 — Produce an output from a working tree with one command** — `user_requirement`, status `ratified`

> From a directory holding a graph, or from any directory beneath it, one command names a format and writes one file, or one folder when asked. It works on a tree with uncommitted changes and on a directory that is not under version control at all.

*Rationale:* The graph a person is writing is the one they want to see rendered, and it is not yet committed. Requiring a commit first, or a push, puts the check after the decision it should inform.

*Derives from:* INT-0001

**origin**: ai · **verification**: Run the command on a graph with an uncommitted edit and on a copy outside git. Each produces the file, and each output's provenance says which it was. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:3cf8d1cae9eb2de5c7843800fdd8949c09b35049d262fdac7bd89ce38cf8a773
<!-- tl:end -->

<!-- tl:item UR-0002 -->
**UR-0002 — The same six forms the editor offers** — `user_requirement`, status `ratified`

> Markdown, a folder of notes for a note-taking tool such as Obsidian, CSV, an Excel workbook, a Word document, and a print-ready HTML document. Each holds what the editor's export of the same graph holds: the same items, links, attributes and cited clauses, laid out the same way.

*Rationale:* A reader who was handed a workbook from the editor last week and a workbook from this tool today should not be able to tell which made it. Two shapes for one graph would be two things to explain.

*Derives from:* INT-0001

**origin**: ai · **verification**: For one graph, each output opens in an ordinary reader for that format and lists every item the graph holds. A notes output has one note per item and no wikilink that names no note. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:441c3e12f160a1d6e395b16ef26ee59e3a83f87ec69b89dc1d38727383c57022
<!-- tl:end -->

<!-- tl:item UR-0003 -->
**UR-0003 — An output says what it was true of** — `user_requirement`, status `ratified`

> Every output names the repository, the ref, the commit and the tool that produced it, and says whether the working tree was clean, had uncommitted changes, or was not under version control.

*Rationale:* An output outlives the tree that made it. An output of an uncommitted graph is useful and must say what it is, because a reader holding the file cannot tell.

*Derives from:* INT-0001

**origin**: ai · **verification**: The provenance lines of an output from a clean tree, a tree with an edit, and a folder outside git read differently, and each is right. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:5874c3937f9d7fc47b61fe150059ea6b758f08f0673cbcb40eacb1e1dbbd285c
<!-- tl:end -->

<!-- tl:item UR-0004 -->
**UR-0004 — A front end that lays out its own pages takes the document's structure from the tool** — `user_requirement`, status `ratified`

> A caller that renders a document itself — the editor lays the PDF's pages out in the browser so its contents can carry page numbers — can ask for the document's structure as data: the title, the front matter, each heading with its level, each item heading with its identifier, type and status, each quotation, paragraph, attribute line and table, and each appendix with where its source comes from. It is the same structure the Word and HTML outputs are built from.

*Rationale:* The editor's PDF is laid out by the browser's own engine so that the page numbers in the contents are the numbers on the pages. That cannot be done from an HTML file, and it must not be done by the editor reading the tool's Markdown, which is the second reading of the tool's shape this package exists to remove.

*Derives from:* INT-0002

**origin**: ai · **verification**: The blocks output for the fixture parses as JSON, carries one item entry per item with its identifier, type and status, and matches the headings the docx output carries. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:a3fd3f45e87a3ce64e171eb1fd2a11e45a0aa007ece9f0a24e241f0a45ddc8d1
<!-- tl:end -->


<!-- tl:item UR-0005 -->
**UR-0005 — A caller that knows the repository, ref and commit states them** — `user_requirement`, status `ratified`

> A caller that holds the graph's repository, ref, commit and working-tree state — the editor has them from the clone, and has no git to ask — can state them, and the output carries what was stated. Git is not consulted when they are given.

*Rationale:* Under Pyodide there is no git. Left to itself the tool would report a graph the editor cloned at a known commit as not under version control, which is the one thing SR-0066 in the editor's graph forbids an export to get wrong.

*Derives from:* INT-0002

**origin**: ai · **verification**: With the four provenance flags given, the output's provenance lines carry the stated values, and no git command is run. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:dd5ac1f1953237d7c7de847229567eafe015a3300d1e49f31406692dd47c5479
<!-- tl:end -->


<!-- tl:item UR-0006 -->
**UR-0006 — The tool runs where there are no processes** — `user_requirement`, status `ratified`

> On a platform that cannot start a process, such as Python under Pyodide in a browser, the tool still reaches tl and tl-compose, and every output is produced exactly as it is from a terminal.

*Rationale:* The editor runs Python in a Web Worker under Pyodide, which has no fork and no exec. A tool that can only spawn a command cannot run there at all.

*Derives from:* INT-0002

**origin**: ai · **verification**: With the platform reported as emscripten, every format for the fixture is produced and matches the output produced through the command. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:3888eca1b900b5b05449ee093d3641ce63d26e5041e240b0517bb65e32de641d
<!-- tl:end -->



## System requirements

How the tool does it. Each implements a user requirement; several read a clause of throughline's own graph, cited as `tl:SR-…`.

<!-- tl:item SR-0001 -->
**SR-0001 — The entry point is decided by the graph, and the tool is run as a command** — `system_requirement`, status `implemented`

> A graph whose configuration declares sources is read through tl-compose; any other through tl. The tool is found beside this package's interpreter first and on the path second, and is run as a command with -C pointing at the graph. Its modules are never imported for their functions. On a platform without processes the console entry point the package declares is called in-process instead (SR-0014).

*Rationale:* Over a composed graph the core command exits cleanly and writes a borrowed clause as its synthetic uid alone, dropping the reference number a conformance document exists to carry. The command line is the surface the tool publishes; its modules move between releases, and an import that worked last month is how a sibling package stopped starting.

*Implements:* UR-0002
*Satisfies:* tl:SR-0187

**origin**: ai · **priority**: must · **verification**: On the composed fixture the Markdown carries the borrowed clause as src:SR-0001 and mirrors it. On the plain fixture the core command is run. Removing the tool from the path produces one line saying so. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:d7e0fd0816f8f13e8fdb2b66ef32fe05ccb47c4147c82609b12da9b58ff7ca37
<!-- tl:end -->

<!-- tl:item SR-0002 -->
**SR-0002 — The Markdown is asked of tl docs over a document of directives** — `system_requirement`, status `implemented`

> The Markdown output is a document of tl directives — a summary, a table of items, one traceability matrix per grounding link type, a catalogue of every item, and the mirrored clauses of adopted sources when the graph composes — handed to the docs command, written outside the graph, and read back. The region markers are stripped unless asked to stay.

*Rationale:* The alternative is rendering items here, which NG-0001 refuses. Written outside the graph so an output can never be mistaken for a change to it.

*Implements:* UR-0002
*Satisfies:* tl:SR-0111, tl:SR-0113

**origin**: ai · **priority**: must · **verification**: The Markdown for the fixture holds the catalogue block of every item, a block this package has no code to produce. With --markers the region markers are present; without, none. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:5916267f5d0db1c4daa658ae5659d2d3d805e3cb21e41104f3b829049918293f
<!-- tl:end -->

<!-- tl:item SR-0003 -->
**SR-0003 — The tool's shape is read in one place** — `system_requirement`, status `implemented`

> The item line, the attribute line and the identifier pattern the tool writes are defined once and read by every writer that cuts or reshapes the tool's Markdown. If the tool changes a line, every output falls back the same way.

*Rationale:* The document formats and the notes both cut the catalogue at the item line. Two definitions of that line is how they would come to disagree about where an item starts.

*Implements:* UR-0002
*Satisfies:* tl:SR-0111

**origin**: ai · **priority**: should · **verification**: One module holds the patterns. A search of the package finds no second definition of the item line. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:ce5afe7aa1f654996f709ebb2fcd64b499883ed6d13aa94da32e4064ea156a45
<!-- tl:end -->

<!-- tl:item SR-0004 -->
**SR-0004 — Provenance is read from git and judged over the graph alone** — `system_requirement`, status `implemented`

> The repository name is read from the origin remote, or failing that the top-level directory's name; the ref from HEAD; the commit from HEAD; and cleanliness from git status over the graph's directory only. Without a repository the tree is reported as not under version control. Without a commit it is reported as holding uncommitted changes.

*Rationale:* Judged over the graph's directory, not the whole repository, because an output is of the graph and a change elsewhere does not alter what it says.

*Implements:* UR-0003

**origin**: ai · **priority**: must · **verification**: A fixture copied into a repository reports clean; after an edit to one item it reports uncommitted changes with the same commit; outside git it reports not under version control with no ref and no commit. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:249b07d7ebede023ddc29df6e3f265616758b185927a43ed4619fe832c3ad6ed
<!-- tl:end -->

<!-- tl:item SR-0005 -->
**SR-0005 — A tabular output is one row per item, over the columns the graph declares** — `system_requirement`, status `implemented`

> csv and xlsx put each item on a row. The columns are the uid, register, type, status, title, text, rationale and normative flag every item has, then each attribute any item in the table carries, then one column per link type listing the targets. The column set is read from the tool's export, never fixed here. One table for everything, or one per register with only the columns its own items use.

*Implements:* UR-0002
*Satisfies:* tl:SR-0055

**origin**: ai · **priority**: must · **verification**: An attribute the package has no knowledge of appears as a populated column. Per register, the Intents table carries no priority column. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:67277d2f6dbd425c9176fd872dd8b2e88a4e6be75eb90b8621fcc62c9d274f00
<!-- tl:end -->

<!-- tl:item SR-0006 -->
**SR-0006 — A links table names both ends of every link by the sheet each is on** — `system_requirement`, status `implemented`

> Beside the item tables, one table holds one row per link: the sheet and uid it starts from, the link type, and the sheet and uid it points at. A link into an adopted source names the namespace as the sheet. The rows are in item order.

*Rationale:* A reviewer follows what rests on what. A links table can be sorted and filtered by either end; a link listed in a cell cannot.

*Implements:* UR-0002

**origin**: ai · **priority**: must · **verification**: Per register, a relates link between two system requirements names System requirements at both ends; a satisfies link into a source names the namespace. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:43c700f598f7814de525dd8e84151adbe8128e9cec9a8996b183b21e5b78540c
<!-- tl:end -->

<!-- tl:item SR-0007 -->
**SR-0007 — Cited clauses travel with the export, and the workbook is read-only** — `system_requirement`, status `implemented`

> The clauses of adopted sources that some item links to travel as one table per source, with the columns those clauses carry. The workbook opens read-only by recommendation with its structure locked and no password, and every sheet still sorts and filters. The csv archive says it cannot be protected.

*Rationale:* An export is a record handed to people who did not make it. A copy edited on its way round is no longer a record of anything. csv has no protection, so the archive says so rather than leaving a reader to assume.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: The composed fixture's workbook holds a sheet named by the namespace with exactly the cited clause. The workbook XML carries read-only recommended, structure lock, and sort and filter allowed. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:8f54e2a4d79e1e2da0bfdc82212ede313e62a42bb6e893358600dbee44d5f9d8
<!-- tl:end -->

<!-- tl:item SR-0008 -->
**SR-0008 — A document output reads as a document** — `system_requirement`, status `implemented`

> The Word and HTML outputs open with a title page naming the provenance, then a contents list, then a section per register with a heading per item carrying its identifier and title, its type and status beneath, its words as a quotation, its rationale, and its attributes in smaller type. Cited clauses follow as one appendix per source with where the source comes from beneath its title. The Word contents is a field Word fills in. The HTML contents is a list of links; page numbers are the browser's to print.

*Rationale:* The structure is read from the shape of the tool's Markdown (SR-0003), never rendered from the graph. Page numbers in HTML would need a paged-media engine no browser ships for print; the browser's own header and footer number the pages.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: The Word document carries Heading2 through Heading4 styles, a TOC field, and a page break per section. The HTML page holds one section per item, a contents list of anchors, and an A4 page rule. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:a7d75e08596a7b76fa757dff4add5375f45f34699229f7da388f75879567939b
<!-- tl:end -->

<!-- tl:item SR-0009 -->
**SR-0009 — A notes output is one note per item, cut from the catalogue, with wikilinks** — `system_requirement`, status `implemented`

> The catalogue and the mirrored clauses are written once and cut at the item line into one Markdown note per item, in a folder per register named by the register's title; cited clauses go under sources, one folder per namespace, with the colon of the identifier replaced by a space in the file name. Each note opens with YAML front matter holding type, status, normative flag and attributes as properties, the title as an alias, and a tag for the type and one for the status. The body is the tool's block reshaped for a note. The item line becomes a level-one heading of the identifier and title, with the type and status on the line beneath. The words, the rationale and the outgoing link lines follow as the tool wrote them. Then one line per incoming link type lists the items that link to this one, worded as the link type reads with the word this — Implements this, Derives from this — so a reader sees what rests on the item without opening a pane. The attribute line is left out, because the front matter already carries every attribute. Every identifier that names a note becomes a wikilink; a clause link shows the identifier the tool wrote as its text. A bracket pair the tool wrote in prose is escaped. An About note carries the provenance.

*Rationale:* The same folder shape the editor produced, so a vault from either opens the same way. The colon is replaced because a note tool refuses one in a name and links by basename across the whole vault. Brackets in prose are escaped because an item that says declare it in [[sources]] would otherwise draw a ghost note. Two decisions were reversed on first real use in Obsidian. The incoming links had been left to the note tool's backlinks pane; a reader of a requirement wants what rests on it in the note itself, and the pane is closed by default and names no link type. The item line and the attribute line had been kept as the tool wrote them; a bold line is not how a note tool shows a title, and the attributes were already the note's properties, so the heading is the note's and the attribute line goes.

*Implements:* UR-0002

**origin**: ai · **priority**: should · **verification**: For the fixtures, one note per item under its register's folder; each note opens with a level-one heading of its identifier and title and a line with its type and status; front matter parses as YAML with the item's properties and no attribute line follows the body; an item that something implements carries an Implements this line naming it as a wikilink; every wikilink names a note in the folder; the TOML brackets are escaped; a clause note is named with a space where the colon was. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:1bef3f4c748adc485b6f989a76d8007763cf21c8ddd0a762a76dd450c2517374
<!-- tl:end -->

<!-- tl:item SR-0010 -->
**SR-0010 — No dependency beyond the throughline family and the standard library** — `system_requirement`, status `implemented`

> The package depends on throughline and throughline-compose and nothing else. xlsx and docx are written from their own specifications over the standard library's zip module. There is no PDF writer (NG-0002).

*Rationale:* Every dependency is one more thing to audit for a tool people install with pipx to run over their own requirements. The cost of writing two Office formats by hand is a few hundred lines already proven in the editor.

*Implements:* UR-0001

**origin**: ai · **priority**: must · **verification**: The dependency list in pyproject.toml names the two packages only. The Office outputs open in LibreOffice. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:28f9f34e41dc05bd7f10bf219fe526106ba999073d302c3fe52e85dc31f2b55e
<!-- tl:end -->

<!-- tl:item SR-0011 -->
**SR-0011 — One file per run, a folder when asked, the same bytes for the same graph** — `system_requirement`, status `implemented`

> Every format writes one file. The notes and csv outputs are a zip by default, or the files written into a folder with --folder. When no name is given one is chosen from the provenance. Zip timestamps are fixed at the format's epoch, so the same graph exported twice gives identical bytes. A path that would escape the folder is refused. A wrong directory, a tool that refuses, or a file that cannot be written is one line on stderr and exit code 1; a usage error is exit code 2.

*Rationale:* An output that differs only in when it was taken cannot be compared with the one before it, and comparing them is what people do with a specification.

*Implements:* UR-0001

**origin**: ai · **priority**: should · **verification**: Each format writes a file that opens; --folder unpacks the vault; two runs over one graph are byte-identical; a directory without a graph gives one line on stderr and exit 1; --folder on xlsx exits 2. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:288caa80a8c8f4f9faae9bcdd26baf94e5183f2ecbb520431f90e1ddd4d27b9c
<!-- tl:end -->

<!-- tl:item SR-0012 -->
**SR-0012 — The blocks output is the document's structure as JSON** — `system_requirement`, status `implemented`

> The blocks format writes one JSON document holding the provenance and the list of blocks the Word and HTML outputs are built from, in order. Each block carries its text and, where present, its heading level, whether it is a quotation, small print or front matter, whether it opens a group, its subtitle, its item's identifier, type and status, and its table's header and rows. Absent fields are omitted. The prose options of the document formats apply to it.

*Rationale:* The same list the two document writers consume, so a front end laying out pages from it cannot disagree with them about the document. JSON because every front end reads it and nothing here has to be invented.

*Implements:* UR-0004
*Relates:* SR-0008

**origin**: ai · **priority**: must · **verification**: tl-transform blocks over the fixture yields JSON whose blocks list has one entry with an item field per item, whose headings agree with the docx output, and whose provenance matches the other outputs. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:8e6c1a1311ddea7b2b9342bccfe5d5f5ea90b7d142a89971b81368e0d0010279
<!-- tl:end -->


<!-- tl:item SR-0013 -->
**SR-0013 — Provenance flags replace the git reading when given** — `system_requirement`, status `implemented`

> The options --repository, --ref, --commit and --tree state the provenance. When any of them is given, git is not run; an unstated ref or commit is none, and an unstated tree is not under version control. --tree accepts clean, dirty and untracked, written into the output in the words the git reading uses.

*Rationale:* Four flags rather than one blob, because a caller reads them back in a shell history. Any one of them given means the caller knows better than git, so git is not asked at all rather than merged with what was stated.

*Implements:* UR-0005
*Refines:* SR-0004

**origin**: ai · **priority**: must · **verification**: Run over a git working tree with --repository x/y --ref v1 --commit abc --tree clean, the output names x/y, v1, abc and clean; run with --repository alone, ref and commit read none and the tree reads not under version control. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:5270fc2db0a7f1fdb7df3da851c7711c4dc03d8ed2e7b3ce7cd93c8f81ec1563
<!-- tl:end -->


<!-- tl:item SR-0014 -->
**SR-0014 — Without processes, the tool calls the console entry point the package declares** — `system_requirement`, status `implemented`

> Where the platform reports itself as emscripten, or a process cannot be started, the tool loads the console entry point that throughline or throughline-compose declares in its package metadata under the name tl or tl-compose, calls it in-process with the same argument vector, and captures its standard output and error. A SystemExit is read as the exit code. Everywhere else the command is spawned as SR-0001 says.

*Rationale:* The console entry point is declared in the package's own metadata and is what the tl command itself runs, so calling it is the command by another route. It is not an import of the tool's modules for their functions. Kept to platforms without processes, so on a terminal the contract of SR-0001 is unchanged.

*Implements:* UR-0006
*Refines:* SR-0001

**origin**: ai · **priority**: must · **verification**: With sys.platform patched to emscripten, dump and docs succeed for the fixtures and the outputs equal those produced by spawning the command; the entry point is resolved from package metadata, not from a module path written here. · **ratified_by**: Henry Grech-Cini · **ratified_fingerprint**: sha256:3f55982a5e7505b84eb345b1c3da6367319c573c7ede94e5672e11ac4d53943d
<!-- tl:end -->



## Traceability

### implements

<!-- tl:matrix incoming:implements links.incoming('implements') -->
| UID | Title | Implements (incoming) |
|---|---|---|
| UR-0001 | Produce an output from a working tree with one command | SR-0010, SR-0011 |
| UR-0002 | The same six forms the editor offers | SR-0001, SR-0002, SR-0003, SR-0005, SR-0006, SR-0007, SR-0008, SR-0009 |
| UR-0003 | An output says what it was true of | SR-0004 |
| UR-0004 | A front end that lays out its own pages takes the document's structure from the tool | SR-0012 |
| UR-0005 | A caller that knows the repository, ref and commit states them | SR-0013 |
| UR-0006 | The tool runs where there are no processes | SR-0014 |
<!-- tl:end -->

### derives from

<!-- tl:matrix incoming:derives_from links.incoming('derives_from') -->
| UID | Title | Derives_from (incoming) |
|---|---|---|
| INT-0001 | The outputs of a graph come from the graph on disk, committed or not | UR-0001, UR-0002, UR-0003 |
| INT-0002 | One implementation of every form, for the command line and the editor alike | UR-0004, UR-0005, UR-0006 |
<!-- tl:end -->
