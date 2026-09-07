# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""A word when a step is slow (SR-0015).

The command says nothing while a step is quick. When a step has run for a
second and not finished, one line on stderr names it, so a composed graph
fetching its sources for the first time does not read as a hang. Never on
stdout, so a script capturing the output is unaffected; never where there are
no threads, which is Pyodide, where the caller shows its own progress.
"""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from typing import Iterator

#: How long a step may run in silence.
SLOW_AFTER = 1.0


def has_threads() -> bool:
    """Whether a timer can run beside the step at all."""
    return sys.platform != "emscripten"


@contextmanager
def slow(message: str, after: float | None = None) -> Iterator[None]:
    """Say ``message`` on stderr if the enclosed step is still running after ``after`` seconds."""
    timer: threading.Timer | None = None
    if has_threads():
        timer = threading.Timer(SLOW_AFTER if after is None else after, _say, args=(message,))
        timer.daemon = True
        try:
            timer.start()
        except RuntimeError:  # a platform that has the module but cannot start a thread
            timer = None
    try:
        yield
    finally:
        if timer is not None:
            timer.cancel()


def _say(message: str) -> None:
    print(f"tl-transform: {message}", file=sys.stderr, flush=True)
