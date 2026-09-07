# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""What an output was taken from (SR-0004).

An output outlives the working tree that made it, and the first question anyone
asks of one is what it was true of. A commit answers that when there is one. A
tree with uncommitted changes, or none under version control at all, is still a
graph worth exporting — the output has to say which it was, because a reader
holding the file cannot tell.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

CLEAN = "clean"
DIRTY = "uncommitted changes"
UNTRACKED = "not under version control"

#: The words a caller may state the tree in, and what each is written as.
TREE_WORDS = {"clean": CLEAN, "dirty": DIRTY, "untracked": UNTRACKED}


@dataclass(frozen=True)
class Provenance:
    repository: str
    ref: str
    commit: str
    tree: str
    tool: str

    def lines(self) -> list[str]:
        return [
            f"Repository: {self.repository}",
            f"Ref: {self.ref or 'none'}",
            f"Commit: {self.commit or 'none'}",
            f"Working tree: {self.tree}",
            f"Produced by: {self.tool}",
        ]

    @property
    def stem(self) -> str:
        """A file name stem: the repository and the ref, made safe for a file name."""
        base = self.repository.replace("/", "-")
        if self.ref:
            base = f"{base}-{self.ref}"
        return re.sub(r"[^\w.-]", "-", base).strip("-") or "graph"


def _git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8"
        )
    except OSError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


_REMOTE = re.compile(r"(?:[:/])([^/:]+/[^/]+?)(?:\.git)?/?$")


def _repository_name(remote: str | None, toplevel: Path) -> str:
    if remote:
        match = _REMOTE.search(remote)
        if match:
            return match.group(1)
    return toplevel.name


def provenance_of(root: Path, tool: str) -> Provenance:
    """Read the working tree's state for the graph at ``root``.

    Cleanliness is judged over the graph's directory, not the whole repository:
    an output is of the graph, and a change elsewhere in the repository does not
    alter what it says.
    """
    toplevel = _git(root, "rev-parse", "--show-toplevel")
    if not toplevel:
        return Provenance(repository=root.name, ref="", commit="", tree=UNTRACKED, tool=tool)
    top = Path(toplevel)
    repository = _repository_name(_git(root, "remote", "get-url", "origin"), top)
    ref = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""
    if ref == "HEAD":
        ref = "detached"
    commit = _git(root, "rev-parse", "HEAD") or ""
    status = _git(root, "status", "--porcelain", "--", str(root))
    tree = DIRTY if status else CLEAN
    if not commit:
        tree = DIRTY
    return Provenance(repository=repository, ref=ref, commit=commit, tree=tree, tool=tool)


def stated(
    tool: str,
    repository: str | None,
    ref: str | None,
    commit: str | None,
    tree: str | None,
) -> Provenance:
    """Provenance as the caller states it (SR-0013). Git is not consulted.

    A caller that gives any of the four knows better than git — the editor
    holds them from the clone and has no git to ask — so nothing is merged
    with a reading; what is unstated is none, and an unstated tree is not
    under version control.
    """
    return Provenance(
        repository=repository or "graph",
        ref=ref or "",
        commit=commit or "",
        tree=TREE_WORDS[tree] if tree else UNTRACKED,
        tool=tool,
    )
