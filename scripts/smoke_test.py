"""
Smoke test: insert one sentence, query it, verify the full pipeline works.
Run inside the askme container: uv run python scripts/smoke_test.py
"""

import asyncio
import os

from askme.rag import create_rag, make_query_param


TEXT = (
    "Scanpy is a scalable toolkit for analyzing single-cell gene expression data. "
    "It includes preprocessing, visualization, clustering, and trajectory inference."
)
QUERY = "What is scanpy used for?"


async def main() -> None:
    os.makedirs("/usr/askme/data/rag_storage", exist_ok=True)

    print("Initializing LightRAG...")
    rag = create_rag()
    await rag.initialize_storages()

    print("Inserting test document...")
    await rag.ainsert(TEXT)

    print(f"\nQuerying: {QUERY!r}\n")
    response = await rag.aquery(QUERY, param=make_query_param(mode="hybrid"))
    print("Response:", response)

    await rag.finalize_storages()
    print("\nSmoke test passed.")


if __name__ == "__main__":
    asyncio.run(main())
