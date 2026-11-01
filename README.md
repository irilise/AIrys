# AIrys

AIrys helps with the clerical overhead of everyday life: keeping track of
appointments, remembering to eat, and managing the small responsibilities that
add up.

AIrys is a local-first personal assistant. It combines a FastAPI backend, a
React/Vite web interface, Ollama for chat generation, and ChromaDB plus local
JSON files for persistent conversation history and semantic memory.

## Current project state

The repository includes an end-to-end single-user assistant:

- **Chat and history:** A React chat interface sends messages to Ollama,
  includes recent turns and relevant saved memories, and restores the local
  conversation after a restart.
- **Memory management:** Save, search, list, and delete categorized memories
  from the interface. ChromaDB stores semantic vectors; JSON files store
  memory metadata and conversation history.
- **Runtime settings:** Change the Ollama host, chat model, temperature, and
  response limit in the settings UI. Changes are saved locally and apply to
  new requests immediately.
- **Development and deployment scaffolding:** The repo includes setup scripts,
  a Makefile, a backend Dockerfile, and a Docker Compose configuration.

AIrys is intended for one local user and does not provide authentication or
production-grade access controls. Keep the backend bound to localhost unless
you have configured appropriate network protections.

## Architecture

```text
React + Vite frontend (port 3000)
        | /api requests via Vite proxy
        v
FastAPI backend (port 7860)
        | chat generation             | embeddings / semantic search
        v                              v
      Ollama                    ChromaDB + local JSON files
```

The main code areas are:

- [`backend/server.py`](./backend/server.py) — FastAPI application and route
  registration.
- [`backend/api/`](./backend/api/) — chat and memory endpoints and Pydantic
  schemas.
- [`backend/memory/`](./backend/memory/) — ChromaDB wrapper and JSON file
  storage.
- [`config/app_config.py`](./config/app_config.py) — environment-based
  settings and default values.
- [`frontend/src/`](./frontend/src/) — React application and chat, memory, and
  settings UI.

## Requirements

- Python 3.10, 3.11, or 3.12 (the supported versions checked by
  [`setup.sh`](./setup.sh))
- Node.js and npm
- [Ollama](https://ollama.com/) with a model available locally

The default configuration expects Ollama at `http://localhost:11434` and the
`llama3.2` model. Set `OLLAMA_HOST` and `OLLAMA_MODEL` to use another Ollama
instance or model.

## Run locally

From the repository root:

1. Copy the example environment file and adjust it if needed:

   ```sh
   cp .env.example .env
   ```

2. Install backend dependencies and create the local data directories:

   ```sh
   bash setup.sh
   ```

   Alternatively, install dependencies from
   [`requirements.txt`](./requirements.txt) with
   `pip install -r requirements.txt`.

3. Ensure Ollama is running (start `ollama serve` in a separate terminal if
   needed), then download the configured model:

   ```sh
   ollama pull llama3.2
   ```

4. In a terminal, start the backend from the repository root:

   ```sh
   python backend/server.py
   ```

5. In another terminal, install frontend dependencies and start Vite:

   ```sh
   cd frontend
   npm install
   npm run dev
   ```

   Open the URL printed by Vite (the configured development port is `3000`).
   Vite proxies `/api` requests to `http://127.0.0.1:7860`.

The backend API documentation is available at `http://127.0.0.1:7860/docs`
when the server is running.

### Optional Docker Compose setup

With Docker Compose and Ollama available on the host, start both app services
from the repository root:

```sh
docker compose up --build
```

Open `http://localhost:3000`. The frontend development server proxies API
requests to the backend container. Ollama remains on the host and is reached
through `host.docker.internal`; set `OLLAMA_HOST_DOCKER` if it is listening at
a different host URL. This container-specific variable avoids using
`localhost` inside the backend container, where it would refer to the
container itself.

With the services running, verify the frontend and backend independently
or run the end-to-end Ollama chat check:

```sh
make smoke-frontend
make smoke-backend
make smoke-integration
# Or run all three checks:
make smoke-test
```

The integration check uses the configured chat model if it is installed in
the local Ollama server; otherwise it selects another installed chat model.
If Ollama has no chat model, it downloads `llama3.2:1b` (override with
`OLLAMA_TEST_MODEL`). During the chat check, the backend's model setting is
temporarily switched if needed and restored afterward. The smoke-test chat
exchange is not added to saved history. Set `AIRYS_FRONTEND_URL`,
`AIRYS_BACKEND_URL`, or `OLLAMA_TEST_HOST` to target services at non-default
URLs; use `OLLAMA_TEST_TIMEOUT` to adjust the model download timeout.

## Configuration and local data

Settings are loaded from environment variables and, when present, `.env`.
The defaults are defined in [`config/app_config.py`](./config/app_config.py);
the starter values are in [`.env.example`](./.env.example). Common settings
include:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default chat model |
| `HOST` | `127.0.0.1` | Backend bind address |
| `PORT` | `7860` | Backend port |
| `DATA_DIR` | `./data` | Root for local application data |
| `CONVERSATIONS_DIR` | `./data/conversations` | Conversation and memory metadata |
| `EMBEDDINGS_DIR` | `./data/embeddings` | Persistent ChromaDB data |
| `EMBEDDING_MODEL` | (unset) | Optional Ollama embedding model (for example `nomic-embed-text`) |

`ALLOWED_ORIGINS` is a JSON array, as shown in `.env.example`. The settings UI
stores its Ollama and inference configuration in `data/settings.json`;
environment variables provide the initial values before settings are saved.
If `EMBEDDING_MODEL` is unset or unavailable, AIrys uses the
`all-MiniLM-L6-v2` sentence-transformers fallback. To use Ollama embeddings,
pull an embedding model and set `EMBEDDING_MODEL` in `.env`. Embedding
configuration is separate from the chat model so changing the chat model
does not change existing memory vector dimensions.

Data is intended to remain local and is ignored by Git. Back up `data/` if you
need to preserve conversations or memories.

## API overview

The API is versioned under `/api/v1`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service information |
| `GET` | `/api/v1/chat/health` | Backend liveness check |
| `POST` | `/api/v1/chat/complete` | Generate a chat reply |
| `GET` | `/api/v1/chat/history` | Load saved conversation exchanges |
| `DELETE` | `/api/v1/chat/history` | Clear the local conversation |
| `GET` | `/api/v1/settings` | Read active Ollama and inference settings |
| `PUT` | `/api/v1/settings` | Validate, save, and apply settings |
| `POST` | `/api/v1/memory/store` | Store a memory (JSON `content` and optional `category`) |
| `GET` | `/api/v1/memory/search` | Search memories by semantic similarity |
| `GET` | `/api/v1/memory/list` | List memories, optionally filtered by category |
| `GET` | `/api/v1/memory/categories` | Return memory categories |
| `DELETE` | `/api/v1/memory/clear/{memory_id}` | Delete one memory |
| `DELETE` | `/api/v1/memory/clear-all` | Delete all memories |

Chat requests accept a `message` and optional `context` and `system_prompt`.
Chat generation is non-streaming. Set `persist_history` to `false` for a
one-off response that is not added to local conversation history. Memory writes
accept JSON, while the previous `memory_content` query parameter remains
supported for compatibility.

## Development commands

From the repository root:

```sh
make help           # Show available Make targets
make run-server     # Start the backend
make run-frontend   # Start the frontend dev server
make build          # Build the frontend
make test           # Run backend unit tests
```
