import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

from askme.config import settings

# Dimensions for known embedding models — tied to the model, not config
_EMBEDDING_DIMS: dict[str, int] = {
    "nomic-embed-text": 768,
    "bge-m3": 1024,
    "all-minilm": 384,
}


def _embedding_dim() -> int:
    for model, dim in _EMBEDDING_DIMS.items():
        if model in settings.embedding_model:
            return dim
    return settings.embedding_dim  # fallback to config


def _make_embedding_func() -> EmbeddingFunc:
    dim = _embedding_dim()

    async def _embed(texts: list[str]) -> np.ndarray:
        # Call the raw function directly — ollama_embed is wrapped with
        # embedding_dim=1024 (bge-m3 default), which would fail for nomic-embed-text
        return await ollama_embed.func(
            texts,
            embed_model=settings.embedding_model,
            host=settings.ollama_host,
            timeout=settings.llm_timeout,
        )

    return EmbeddingFunc(
        embedding_dim=dim,
        max_token_size=8192,
        func=_embed,
        model_name=settings.embedding_model,
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
        kv_storage="JsonKVStorage",
        doc_status_storage="JsonDocStatusStorage",
    )


def make_query_param(**kwargs) -> QueryParam:
    mode = kwargs.pop("mode", settings.default_query_mode)
    return QueryParam(mode=mode, **kwargs)
