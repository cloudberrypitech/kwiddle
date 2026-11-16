"""Small, dependency-free helpers for Kwiddle's reader enhancements."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

_PROGRESS_FILE = Path.home() / ".local" / "share" / "kwiddle" / "reading-progress.json"


def load_progress(key: str) -> dict:
    """Load saved reading state for a document, returning an empty state safely."""
    try:
        data = json.loads(_PROGRESS_FILE.read_text(encoding="utf-8"))
        value = data.get(key, {})
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_progress(key: str, **values) -> None:
    """Persist reading state atomically without requiring elevated permissions."""
    try:
        _PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(_PROGRESS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        data[key] = {**(data.get(key, {}) if isinstance(data.get(key), dict) else {}), **values}
        temporary = _PROGRESS_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temporary.replace(_PROGRESS_FILE)
    except OSError:
        # Reading must continue to work even on read-only or portable installs.
        return


def document_headings(document) -> list[tuple[str, int]]:
    """Return heading labels and their outline levels for a simple document outline."""
    result = []
    for block in getattr(document, "blocks", []):
        if getattr(block, "kind", "") == "heading":
            try:
                level = int(block.attributes.get("outline_level") or 1)
            except (TypeError, ValueError, AttributeError):
                level = 1
            label = (getattr(block, "text", "") or "").strip()
            if label:
                result.append((label, max(1, min(level, 6))))
    return result


def font_inventory(document) -> list[str]:
    """Collect font-family names actually declared by document text runs/styles."""
    fonts = set()
    for block in getattr(document, "blocks", []):
        for style in (getattr(block, "style", None),):
            name = getattr(style, "font", None)
            if name:
                fonts.add(str(name))
        for run in getattr(block, "runs", []):
            name = getattr(getattr(run, "style", None), "font", None)
            if name:
                fonts.add(str(name))
        for child in getattr(block, "children", []):
            for name in font_inventory(type("DocumentView", (), {"blocks": [child]})()):
                fonts.add(name)
    return sorted(fonts, key=str.casefold)


def table_to_rows(table_block) -> list[list[str]]:
    """Convert a kwloader table block into rows of plain cell text."""
    rows = []
    for row in getattr(table_block, "children", []):
        cells = []
        for cell in getattr(row, "children", []):
            cells.append(" ".join(
                (getattr(paragraph, "text", "") or "").strip()
                for paragraph in getattr(cell, "children", [])
            ).strip())
        rows.append(cells)
    return rows


def fit_horizontal_margins(widget, minimum: int = 18, maximum: int = 120) -> int:
    """Center the reading column as the window grows; return the applied margin."""
    try:
        width = max(1, widget.winfo_width())
        # Keep a comfortable measure instead of stretching long lines edge-to-edge.
        margin = max(minimum, min(maximum, (width - 760) // 2))
        widget.configure(padx=margin)
        return margin
    except Exception:
        return minimum
