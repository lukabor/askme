"""
Text extraction from notebook formats.

Supports:
- .ipynb  (Jupyter notebooks)  — extracts markdown + code cells with headers
- .Rmd    (R Markdown)         — strips YAML front-matter, keeps prose + code blocks
- .py     (Python scripts)     — returns source as-is, strips shebangs
- .R      (R scripts)          — returns source as-is

Each extractor returns a plain string ready for LightRAG ingestion.
The path is never read here — callers pass content or a Path object.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


# ── Jupyter notebooks (.ipynb) ────────────────────────────────────────────────

def extract_ipynb(path: Path) -> str:
    """
    Convert a Jupyter notebook to a readable text document.

    Strategy:
    - Markdown cells  → included as-is (prose, explanations)
    - Code cells      → wrapped in a fenced block with language tag
    - Raw cells       → skipped
    - Output text     → included when present (printed results, errors give context)
    - Output images   → skipped (no text value for RAG)

    The notebook filename and cell numbers are prepended so LightRAG can
    extract entities like "in notebook X, step 3 does Y".
    """
    nb = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    lang = (
        nb.get("metadata", {})
        .get("kernelspec", {})
        .get("language", "python")
        .lower()
    )
    parts: list[str] = [f"# Notebook: {path.name}\n"]

    for i, cell in enumerate(nb.get("cells", []), start=1):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))

        if not source.strip():
            continue

        if cell_type == "markdown":
            parts.append(source)

        elif cell_type == "code":
            parts.append(f"```{lang}\n{source}\n```")
            # Include plain-text outputs (stdout, stderr, text/plain)
            output_lines: list[str] = []
            for output in cell.get("outputs", []):
                otype = output.get("output_type", "")
                if otype in ("stream",):
                    output_lines.extend(output.get("text", []))
                elif otype in ("execute_result", "display_data"):
                    data = output.get("data", {})
                    if "text/plain" in data:
                        output_lines.extend(data["text/plain"])
            if output_lines:
                text_out = "".join(output_lines).strip()
                if text_out:
                    parts.append(f"Output:\n{text_out}")

    return "\n\n".join(parts)


# ── R Markdown (.Rmd) ─────────────────────────────────────────────────────────

_YAML_FRONT_MATTER = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_RMD_CODE_FENCE = re.compile(r"```\{[^}]+\}", re.MULTILINE)


def extract_rmd(path: Path) -> str:
    """
    Extract text from an R Markdown file.

    - Strips YAML front matter
    - Keeps prose sections as-is
    - Normalises code fences: ```{r ...} → ```r  (readable but not executed)
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    # Remove YAML front matter
    text = _YAML_FRONT_MATTER.sub("", text, count=1)
    # Normalise code fence headers: ```{r chunk-name, echo=FALSE} → ```r
    text = _RMD_CODE_FENCE.sub(
        lambda m: "```" + re.search(r"\{(\w+)", m.group()).group(1),
        text,
    )
    return f"# Notebook: {path.name}\n\n{text.strip()}"


# ── Python scripts (.py) ──────────────────────────────────────────────────────

_SHEBANG = re.compile(r"^#!.*\n")


def extract_py(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _SHEBANG.sub("", text, count=1)
    return f"# Script: {path.name}\n\n{text.strip()}"


# ── R scripts (.R) ────────────────────────────────────────────────────────────

def extract_r(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    return f"# Script: {path.name}\n\n{text.strip()}"


# ── Dispatcher ────────────────────────────────────────────────────────────────

_EXTRACTORS = {
    ".ipynb": extract_ipynb,
    ".rmd": extract_rmd,
    ".py": extract_py,
    ".r": extract_r,
}


def extract(path: Path) -> str | None:
    """
    Extract text from a supported file. Returns None for unsupported types.
    Raises on read/parse errors so callers can decide whether to skip or abort.
    """
    extractor = _EXTRACTORS.get(path.suffix.lower())
    if extractor is None:
        return None
    return extractor(path)


def supported_suffixes() -> frozenset[str]:
    return frozenset(_EXTRACTORS)
