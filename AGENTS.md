<!--
  This is the CANONICAL agent-guidance document for throughline-transform;
  CLAUDE.md and GEMINI.md point here so there is one source of truth, not N
  drifting copies.
-->

# Working with throughline-transform (for AI agents)

This repository is **throughline-transform**, the command-line tool (`tl-transform`)
that turns a [throughline](https://github.com/rhodium-org/throughline) requirements
graph on disk — committed or not — into the forms its readers open: Markdown, a
folder of Obsidian notes, CSV, an Excel workbook, a Word document, or a print-ready
HTML page. It is compose-aware: a graph that declares `[[sources]]` is read through
[`tl-compose`](https://github.com/rhodium-org/throughline-compose). It is
self-hosting: its own requirements live under [`idd/`](idd).

## Using tl-transform in a project

```bash
pipx install throughline-transform
tl-transform notes -C idd --folder     # a vault to open in Obsidian
tl-transform xlsx  -C idd              # a read-only workbook
tl-transform html  -C idd              # print to PDF from a browser
```

The output is of the working tree as it is. Its provenance says whether the tree
was clean, had uncommitted changes, or was not under version control. An agent
handing an output to a person should say the same.

## Working on this repo

Read [`idd/`](idd) first — run `tl-compose -C idd context` for the generated brief.
Two rules bind every change here:

- **Never render an item's words.** Every word of an item in an output comes from
  `tl docs` ([`NG-0001`](idd/non-goals/NG-0001.yml)). The shape of the tool's
  output is read in one module, `shape.py` ([`SR-0003`](idd/system-requirements/SR-0003.yml)).
- **Add no dependency** beyond `throughline` and `throughline-compose`
  ([`SR-0010`](idd/system-requirements/SR-0010.yml)).
- **The editor runs this package under Pyodide** ([`INT-0002`](idd/intents/INT-0002.yml)).
  Anything that spawns a process, reads git, or touches the file system outside
  the output path must keep working with no processes and with provenance stated
  by the caller (`SR-0013`, `SR-0014`). The `blocks` output is what the editor's
  PDF layout consumes (`SR-0012`); its field names are a contract.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q                                 # the fixture graphs are built by the installed tl
tl-compose -C idd check --strict          # this repo's own graph — keep it green
tl-compose -C idd docs --check            # its published spec — regenerate with `docs`
```

Ground the change in an `idd/` item (create it, and have a human ratify it if
it is AI-origin), cite the UID in the commit, and keep both gates green. The
editor's export ([throughline-editor](https://github.com/rhodium-org/throughline-editor),
`app/src/export/`) is the sibling implementation of these formats; a change to
the shape of an output here should be made there too, or the two will drift.
