"""Quick sanity check for the extractor — prints stats only, no content."""
from pathlib import Path
from askme.ingestion.extract import extract, supported_suffixes

archive = Path("/usr/askme/data/notebook_archive")

for suffix in sorted(supported_suffixes()):
    files = [
        p for p in archive.rglob(f"*{suffix}")
        if "site-packages" not in str(p) and "__pycache__" not in str(p)
        and "x86_64-pc-linux-gnu-library" not in str(p)
    ]
    if not files:
        print(f"{suffix}: no files found")
        continue
    sample = files[0]
    try:
        text = extract(sample)
        lines = text.splitlines() if text else []
        print(f"{suffix}: {len(files)} files | sample '{sample.name}' → {len(text)} chars, {len(lines)} lines")
    except Exception as e:
        print(f"{suffix}: ERROR on '{sample.name}': {e}")
