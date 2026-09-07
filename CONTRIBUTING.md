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

That pulls [throughline-compose][tlc] and [throughline][tl] along too. Python 3.11
or later.

### If you're also working on throughline or throughline-compose

Chain the editable installs in a single command so the resolver never reaches
the package index, then verify every path is your checkout:

```bash
pip install -e ../throughline -e ../throughline-compose -e '.[dev]'
python -c "import throughline as a, throughline_compose as b, throughline_transform as c; \
[print(m.__file__) for m in (a, b, c)]"
```

Mind that `tl-transform` runs `tl` and `tl-compose` as commands found beside its
own interpreter, so the ones in your venv are the ones it uses.

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
tl-compose -C idd check --strict
tl-compose -C idd docs --check
```

## Making a change

1. Ground it. Find or create the `idd/` item the change serves; an AI-authored
   item enters `proposed` and a person ratifies it.
2. Keep the two rules: no rendering of an item's words, no new dependency.
3. If the shape of an output changes, change the editor's export too.
4. Cite the UID in the commit message.

[tl]: https://github.com/rhodium-org/throughline
[tlc]: https://github.com/rhodium-org/throughline-compose
