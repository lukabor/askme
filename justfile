# askme – LightRAG over bioinformatics notebooks
# Usage: just <recipe>

set dotenv-load := true
set shell := ["bash", "-cu"]

# Default: list available recipes
default:
    @just --list

# ── Stack lifecycle ────────────────────────────────────────────────────────────

# Start all services (pulls models on first run)
up:
    docker compose up -d

# Start and stream logs
up-attached:
    docker compose up

# Stop all services
down:
    docker compose down

# Rebuild askme image and restart
build:
    docker compose build askme
    docker compose up -d --no-deps askme

# Restart a single service (default: askme)
restart service="askme":
    docker compose restart {{ service }}

# Show running services and health
ps:
    docker compose ps

# ── Logs ───────────────────────────────────────────────────────────────────────

# Stream logs for all services (or pass a service name)
logs service="":
    docker compose logs -f --tail=100 {{ service }}

# ── Models ────────────────────────────────────────────────────────────────────

# Manually pull/update Ollama models (re-runs ollama-init)
pull-models:
    docker compose run --rm ollama-init

# List models currently loaded in Ollama
list-models:
    docker compose exec ollama ollama list

# ── Ingestion ─────────────────────────────────────────────────────────────────

# Run ingestion pipeline (optional: path relative to data/)
ingest path="notebook_archive":
    docker compose exec askme uv run askme-ingest --source /usr/askme/data/{{ path }}

# ── Querying ──────────────────────────────────────────────────────────────────

# Run a one-off query from the CLI
query q:
    docker compose exec askme uv run askme-query "{{ q }}"

# ── Shells ────────────────────────────────────────────────────────────────────

# Open a shell inside a container (default: askme)
shell service="askme":
    docker compose exec {{ service }} bash

# Open Neo4j cypher shell
neo4j-shell:
    docker compose exec neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-askme_neo4j}

# Open Ollama CLI shell
ollama-shell:
    docker compose exec ollama bash

# ── Data management ───────────────────────────────────────────────────────────

# Wipe vector + graph stores (keeps models). Use when re-ingesting from scratch
clean-stores:
    @echo "WARNING: This will delete all Neo4j and Qdrant data."
    @read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
    docker compose down
    docker volume rm askme_neo4j_data askme_qdrant_data || true
    docker compose up -d

# Full teardown: stop everything and remove all volumes (including models)
clean-all:
    @echo "WARNING: This will delete ALL volumes including downloaded models."
    @read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
    docker compose down -v

# ── Health checks ─────────────────────────────────────────────────────────────

# Check all services are reachable
check:
    @echo "Neo4j...";   curl -sf http://localhost:7474 > /dev/null && echo "  OK" || echo "  FAIL"
    @echo "Qdrant...";  curl -sf http://localhost:6333/healthz > /dev/null && echo "  OK" || echo "  FAIL"
    @echo "Ollama...";  curl -sf http://localhost:11434/api/tags > /dev/null && echo "  OK" || echo "  FAIL"

# ── Info ──────────────────────────────────────────────────────────────────────

# Show service URLs
urls:
    @echo "askme API   → http://localhost:8000"
    @echo "Neo4j UI    → http://localhost:7474"
    @echo "Qdrant UI   → http://localhost:6333/dashboard"
    @echo "Ollama API  → http://localhost:11434"
