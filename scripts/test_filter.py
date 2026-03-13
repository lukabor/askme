"""
Test the filter pipeline: walk the archive, apply path filter + dedup.
Prints stats only — no file content is shown.
"""

from pathlib import Path

from askme.config import settings
from askme.ingestion.extract import extract
from askme.ingestion.filter import Deduplicator, filter_paths

archive = Path("/usr/askme/data/notebook_archive")

all_paths = list(archive.rglob("*"))
kept = filter_paths(all_paths)

print(f"Total files found : {len(all_paths)}")
print(f"After path filter : {len(kept)}")

# Count by type
by_suffix: dict[str, int] = {}
for p in kept:
    by_suffix[p.suffix.lower()] = by_suffix.get(p.suffix.lower(), 0) + 1
for suffix, count in sorted(by_suffix.items()):
    print(f"  {suffix:8s} {count}")

# Run deduplication
dedup = Deduplicator(threshold=settings.minhash_threshold)
duplicates = 0
errors = 0

for path in kept:
    try:
        text = extract(path)
        if not text or not text.strip():
            continue
        if dedup.is_duplicate(path, text):
            duplicates += 1
    except Exception as e:
        errors += 1

print(f"\nAfter dedup (threshold={settings.minhash_threshold}):")
print(f"  Unique documents : {dedup.seen_count}")
print(f"  Duplicates found : {duplicates}")
print(f"  Errors           : {errors}")
