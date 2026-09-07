# throughline-transform

A [throughline](https://github.com/rhodium-org/throughline) requirements graph on
disk — committed or not — in the forms its readers open. One command, one file:

```bash
pipx install throughline-transform      # pulls tl and tl-compose along too

tl-transform md      -C idd             # Markdown, written by the tool itself
tl-transform notes   -C idd             # a folder of notes for Obsidian (zip)
tl-transform notes   -C idd --folder    # …or the folder itself, ready to open as a vault
tl-transform csv     -C idd             # one row per item, a links file, a file per cited source (zip)
tl-transform xlsx    -C idd             # the same as a read-only workbook that still sorts and filters
tl-transform docx    -C idd             # a Word document: title page, contents, a heading per item
tl-transform html    -C idd             # a print-ready page — print it to PDF from any browser
```

It is the command-line half of the
[throughline editor](https://github.com/rhodium-org/throughline-editor)'s export:
the same six forms, laid out the same way, from the graph as it stands on your
disk. The editor needs the graph on GitHub. This does not — it reads the working
tree, and the output says whether that tree was clean, carried uncommitted
changes, or was not under version control at all.

## What it does not do

**It never renders an item's words.** The Markdown is asked of `tl docs` over a
document of directives; the structure is read from `tl dump`. What this package
adds is the containers — a workbook, a Word document, a folder of notes, a
print-ready page — and the front matter and link syntax a note tool reads. If a
requirement here rendered prose, it would drift from what `tl docs --check`
gates, and a document that quietly differs from the published specification is
worse than none. That is [`NG-0001`](idd/non-goals/NG-0001.yml).

**It ships no PDF writer** ([`NG-0002`](idd/non-goals/NG-0002.yml)). Every
browser prints to PDF with a renderer that is already on the machine.

**It depends on nothing but the family.** `throughline` and
`throughline-compose`, and the standard library's `zipfile` for the two Office
formats, which are written from their own specifications.

## Which tool answers

A graph whose `throughline.toml` declares `[[sources]]` is read through
`tl-compose`; any other through `tl`. That is not cosmetic: over a composed graph
the core command exits cleanly and writes a borrowed clause as its synthetic uid
alone, dropping the reference number a conformance document exists to carry.
The tool is found beside this package's interpreter first and on the path
second, and is run as a command — its command line is the surface it publishes.

## The outputs

| Format | What you get |
|---|---|
| `md` | The tool's own document: a summary, a catalogue of every item in full, the mirrored clauses of adopted sources. `--body table` or `both` for a one-line-per-item table, `--matrix` for one traceability matrix per grounding link type, `--markers` to keep the region markers so `tl docs` can refill the file later. |
| `notes` | One Markdown note per item in a folder per register, YAML front matter as properties (type, status, attributes, the title as an alias, a tag each for type and status), every identifier a `[[wikilink]]`. Cited clauses under `sources/<namespace>/`, the colon in their name replaced by a space. Open the folder as an Obsidian vault: the graph view is the intent graph, and a note's backlinks are what rests on it. |
| `csv` | A zip of one file of items (or one per register with `--split per-register`), `links.csv` with one row per link naming the sheet at each end, one file per cited source, and the provenance. |
| `xlsx` | The same as sheets, read-only by recommendation with the structure locked and no password. Sorting and filtering stay allowed; a spreadsheet nobody can sort is one nobody can review. |
| `docx` | A title page with the provenance, a contents field Word fills in, a section per register, a heading per item with its type and status beneath, its words as a quotation, its rationale, its attributes in small print, and one appendix per cited source. |
| `html` | The same document as one self-contained page with print typography, A4 page rules and a contents list of links. Print it to PDF; the browser numbers the pages. |
| `blocks` | The document's structure as JSON — the same list of headings, quotations, paragraphs, attribute lines, tables and appendices the Word and HTML outputs are built from — for a front end that lays out its own pages. The editor's PDF is laid out from it. |

Every output carries the repository, ref, commit, working-tree state and tool
version it was taken from, because an output outlives the tree that made it and
the first question anyone asks of one is what it was true of. A caller that
knows them without git — the editor holds them from its clone — states them with
`--repository`, `--ref`, `--commit` and `--tree clean|dirty|untracked`, and git
is then not consulted.

## One implementation, two surfaces

The [throughline editor](https://github.com/rhodium-org/throughline-editor)
runs this package as a wheel under Pyodide beside `tl` and `tl-compose`, so an
export from a browser tab and an export from a terminal are the same bytes for
the same graph at the same commit. Pyodide has no processes, so there the tool
calls the console entry point `tl` or `tl-compose` declares in its package
metadata — the same function the command runs — instead of spawning it.

## Self-hosting

This repository's own requirements live under [`idd/`](idd) and compose
throughline's graph as a pinned source, so a requirement here can cite the
clause of the tool it reads (`satisfies: tl:SR-0111`) and have the citation
resolved rather than asserted.

```bash
tl-compose -C idd check --strict     # the grounding gate
tl-compose -C idd docs --check       # idd/docs/spec.md must match the graph
tl-transform html -C idd             # and the tool over its own graph
```

Apache-2.0. Created by Dr Henry J Grech-Cini; see [`PROVENANCE.md`](PROVENANCE.md).
