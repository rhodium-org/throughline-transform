# Contributing to throughline-transform

Thanks for your interest. `throughline-transform` is the command-line tool
(`tl-transform`) that turns a [throughline][tl] requirements graph on disk into
the forms its readers open.

Contributions are welcome, including the kind that isn't code: running it over a
real graph and reporting where an output fought you is a genuine contribution.

## Set up your environment

```bash
git clone https://github.com/rhodium-org/throughline-transform.git
cd throughline-transform
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
```

That pulls [throughline][tl] along too. Python 3.11 or later.

### If you're also working on throughline

Chain the editable installs in a single command so the resolver never reaches
the package index, then verify every path is your checkout:

```bash
pip install -e ../throughline -e '.[dev]'
python -c "import throughline as a, throughline_transform as b; \
[print(m.__file__) for m in (a, b)]"
```

Mind that `tl-transform` runs `tl` as a command found beside its own
interpreter, so the one in your venv is the one it uses.

## Run the tests

```bash
python -m pytest
```

The fixture graphs are built by the installed `tl` (`init`, `new`, `link`), never
written by hand, so they cannot drift from the format the tool reads.

## Run the requirements gate

This repository manages its own requirements with the family it belongs to — they
live in [`idd/`](idd) and compose throughline's graph as a pinned source:

```bash
tl -C idd check --strict
tl -C idd docs --check
```

## Making a change

1. Ground it. Find or create the `idd/` item the change serves; an AI-authored
   item enters `proposed` and a person ratifies it.
2. Keep the two rules: no rendering of an item's words, no new dependency.
3. If the shape of an output changes, change the editor's export too.
4. Cite the UID in the commit message.

[tl]: https://github.com/rhodium-org/throughline
