from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768  # nomic-embed-text output dimension
    llm_timeout: int = 300

    # Neo4j
    neo4j_uri: str = "neo4j://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "askme_neo4j"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Storage
    data_dir: str = "/usr/askme/data"
    rag_working_dir: str = "/usr/askme/data/rag_storage"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
