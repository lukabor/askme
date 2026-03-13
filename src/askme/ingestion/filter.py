"""
File filtering and deduplication for the ingestion pipeline.

Two responsibilities:
1. filter_paths()  — decide which files are worth ingesting at all
                     (skip venvs, build artifacts, checkpoints)
2. Deduplicator    — MinHash-based near-duplicate detection across files
                     (same analysis copy-pasted across projects won't be ingested twice)
"""

from __future__ import annotations

from pathlib import Path

from datasketch import MinHash, MinHashLSH

from askme.ingestion.extract import supported_suffixes


# ── Path filter ───────────────────────────────────────────────────────────────

# Directory names that signal the path is inside a venv / package library
# rather than original research code. Any path component matching one of
# these strings is skipped.
_VENV_MARKERS: frozenset[str] = frozenset(
    {
        "site-packages",
        "dist-packages",
        "__pycache__",
        ".ipynb_checkpoints",
        "x86_64-pc-linux-gnu-library",  # R library tree
        "node_modules",
    }
)


def is_venv_path(path: Path) -> bool:
    """Return True if any component of the path looks like a venv/library."""
    return any(marker in path.parts for marker in _VENV_MARKERS)


def filter_paths(paths: list[Path]) -> list[Path]:
    """
    Return only paths that are:
    - A supported file type (.ipynb, .rmd, .py, .r)
    - Not inside a venv, package library, or checkpoint directory
    - Non-empty files
    """
    kept = []
    for p in paths:
        if p.suffix.lower() not in supported_suffixes():
            continue
        if is_venv_path(p):
            continue
        if p.stat().st_size == 0:
            continue
        kept.append(p)
    return kept


# ── MinHash deduplication ─────────────────────────────────────────────────────

_NUM_PERM = 128  # number of permutations — controls accuracy vs speed tradeoff


def _minhash(text: str) -> MinHash:
    """Compute a MinHash signature from a text using word shingles."""
    m = MinHash(num_perm=_NUM_PERM)
    # Use 5-word shingles for semantic similarity
    words = text.lower().split()
    for i in range(max(1, len(words) - 4)):
        shingle = " ".join(words[i : i + 5])
        m.update(shingle.encode("utf-8"))
    return m


class Deduplicator:
    """
    Tracks seen documents and detects near-duplicates using MinHash LSH.

    Usage:
        dedup = Deduplicator(threshold=0.85)
        for path, text in documents:
            if dedup.is_duplicate(path, text):
                continue   # skip
            # ingest this document
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self._lsh = MinHashLSH(threshold=threshold, num_perm=_NUM_PERM)
        self._seen: dict[str, Path] = {}  # key → original path

    def is_duplicate(self, path: Path, text: str) -> bool:
        """
        Returns True if this text is a near-duplicate of a previously seen document.
        Registers the document if it is new.
        """
        key = str(path)
        m = _minhash(text)
        results = self._lsh.query(m)

        if results:
            original = self._seen[results[0]]
            return True

        # New document — register it
        self._lsh.insert(key, m)
        self._seen[key] = path
        return False

    @property
    def seen_count(self) -> int:
        return len(self._seen)
