.PHONY: help install run-server run-frontend start-all build lint test smoke-test smoke-frontend smoke-backend smoke-integration clean

help:
	@echo "AIrys Development Commands:"
	@echo "  make install      Install backend dependencies"
	@echo "  make run-server   Start the backend server"
	@echo "  make run-frontend Start the frontend dev server"
	@echo "  make start-all    Start backend and frontend"
	@echo "  make build        Build the frontend for production"
	@echo "  make lint         Compile Python source files"
	@echo "  make test         Run backend unit tests"
	@echo "  make smoke-test   Smoke-test running frontend, backend, and Ollama chat"
	@echo "  make smoke-frontend  Test the running frontend only"
	@echo "  make smoke-backend   Test the running backend only"
	@echo "  make smoke-integration Test frontend-to-backend chat with local Ollama"
	@echo "  make clean        Remove Python cache files"

install:
	pip install -r requirements.txt

run-server:
	python backend/server.py

run-frontend:
	cd frontend && npm run dev

start-all:
	python backend/server.py &
	cd frontend && npm run dev

build:
	cd frontend && npm run build

lint:
	python -m compileall -q backend config tests

test:
	python -m unittest discover -s tests -v

smoke-test:
	python tests/smoke_test.py --target all

smoke-frontend:
	python tests/smoke_test.py --target frontend

smoke-backend:
	python tests/smoke_test.py --target backend

smoke-integration:
	python tests/smoke_test.py --target integration

clean:
	find backend config tests -type d -name "__pycache__" -exec rm -rf {} +
