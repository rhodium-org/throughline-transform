# Copyright (c) 2026 Henry J Grech-Cini
# SPDX-License-Identifier: Apache-2.0
"""throughline-transform: a throughline graph on disk, in the forms its readers open.

Everything here reads what the tool writes. The Markdown comes from ``tl docs``
over a document of directives; the structure comes from ``tl dump``. What this
package adds is the containers — a workbook, a Word document, a folder of notes,
a print-ready page — and never a second rendering of an item's words.
"""

from .project import TransformError

__all__ = ["TransformError"]
