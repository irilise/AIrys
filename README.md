# AIrys

AIrys is an experiment in building a personal support agent to help with the
clerical overhead of everyday life: keeping track of appointments, remembering
to eat, and managing the small responsibilities that add up.

The current checkout is an early, local-first prototype. It combines a
FastAPI backend, a React/Vite web interface, Ollama for chat generation, and
ChromaDB for persistent semantic memory.

## Current project state

The repository contains the main pieces of a full-stack assistant:

- **Chat UI:** A React interface for composing messages and displaying
  assistant replies, with a backend connection indicator.
- **Local model integration:** The backend sends non-streaming chat requests
  to an Ollama server. The default model is `llama3.2`.
- **Memory components:** API routes support storing, searching, categorizing,
  listing, and deleting memory records. The chat route is intended to retrieve
  related memories and include them as context.
- **Persistence:** ChromaDB stores vectors; JSON files under `data/` are used
  for conversation history and memory metadata.
- **Development and deployment scaffolding:** The repo includes setup scripts,
  a Makefile, a backend Dockerfile, and a Docker Compose configuration.

The feature paths are not yet consistently wired end to end; see
[Current limitations](#current-limitations) before trying the app.

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

## Configuration and local data

Settings are loaded from environment variables and, when present, `.env`.
The defaults are defined in [`config/app_config.py`](./config/app_config.py);
the starter values are in [`.env.example`](./.env.example). Common settings
include:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Model used for chat and Ollama embeddings |
| `HOST` | `127.0.0.1` | Backend bind address |
| `PORT` | `7860` | Backend port |
| `DATA_DIR` | `./data` | Root for local application data |
| `CONVERSATIONS_DIR` | `./data/conversations` | Conversation and memory metadata |
| `EMBEDDINGS_DIR` | `./data/embeddings` | Persistent ChromaDB data |

If you copy `.env.example`, change `ALLOWED_ORIGINS` from its comma-separated
value to a JSON array, for example
`ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:5173"]`,
or remove that setting to use the defaults.

Data is intended to remain local and is ignored by Git. Back up `data/` if you
need to preserve conversations or memories.

## API overview

The API is versioned under `/api/v1`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Basic service information |
| `GET` | `/api/v1/chat/health` | Backend liveness check |
| `POST` | `/api/v1/chat/complete` | Generate a chat reply |
| `POST` | `/api/v1/memory/store` | Store a memory (`memory_content` parameter) |
| `GET` | `/api/v1/memory/search` | Search memories by semantic similarity |
| `GET` | `/api/v1/memory/list` | List memories, optionally filtered by category |
| `GET` | `/api/v1/memory/categories` | Return memory categories |
| `DELETE` | `/api/v1/memory/clear/{memory_id}` | Delete one memory |
| `DELETE` | `/api/v1/memory/clear-all` | Delete all memories |

Chat requests accept a `message` and optional `context` and `system_prompt`.
Chat generation is currently non-streaming.

## Current limitations

The following gaps are visible in the current source and mean the prototype
should not be treated as a working or production-ready assistant:

- [`chat_routes.py`](./backend/api/chat_routes.py) uses `vector_db` and
  `file_storage` without initializing them in that module, so its memory
  retrieval and conversation persistence path is not wired up.
- [`FileStorage`](./backend/memory/storage.py) calls `Path.write_json`, which
  is not provided by Python's standard `pathlib.Path`. The JSON metadata and
  conversation write paths therefore need correction before persistence can
  work.
- The [chat component](./frontend/src/components/ChatInterface.jsx) reads
  `serverStatus` without declaring it or receiving it as a prop, while
  [`App.jsx`](./frontend/src/App.jsx) does not pass it. The
  [settings component](./frontend/src/components/SettingsModal.jsx) also calls
  `toast.success` without importing `toast`; these UI paths need fixes.
- [`memory_routes.py`](./backend/api/memory_routes.py) returns no entries from
  the memory list without a category, and its category-filtered path calls
  `VectorDatabase.get`, which is not implemented.
- The settings form saves values in browser `localStorage`, but the backend
  reads model and host configuration from environment settings; changing those
  form values does not reconfigure the backend.
- The `.env.example` value for `ALLOWED_ORIGINS` is comma-separated text, but
  the setting is a list; as written, the template may fail settings parsing.
- [`docker-compose.yml`](./docker-compose.yml) refers to
  `frontend/Dockerfile.frontend`, which is not present in the repository.
- No automated test files are currently tracked under [`tests/`](./tests/).

## Development commands

From the repository root:

```sh
make help           # Show available Make targets
make run-server     # Start the backend
make run-frontend   # Start the frontend dev server
make build          # Build the frontend
```
