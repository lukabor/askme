import numpy as np
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

from askme.config import settings


def _make_embedding_func() -> EmbeddingFunc:
    async def _embed(texts: list[str]) -> np.ndarray:
        return await ollama_embed(
            texts,
            embed_model=settings.embedding_model,
            host=settings.ollama_host,
            timeout=settings.llm_timeout,
        )

    return EmbeddingFunc(
        embedding_dim=settings.embedding_dim,
        max_token_size=8192,
        func=_embed,
    )


def create_rag() -> LightRAG:
    return LightRAG(
        working_dir=settings.rag_working_dir,
        # LLM
        llm_model_func=ollama_model_complete,
        llm_model_name=settings.llm_model,
        llm_model_kwargs={
            "host": settings.ollama_host,
            "timeout": settings.llm_timeout,
            "options": {"num_ctx": 32768},
        },
        # Embeddings
        embedding_func=_make_embedding_func(),
        # Storage backends
        graph_storage="Neo4JStorage",
        vector_storage="QdrantVectorDBStorage",
        kv_storage="JsonKVStorage",         # lightweight KV — no extra service needed
        doc_status_storage="JsonDocStatusStorage",
    )
