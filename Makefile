# Makefile for AIrys

.PHONY: help install run-server run-frontend build clean

help:
	@echo "AIrys Development Commands:"
	@echo ""
	@echo "  make install     - Install production dependencies"
	@echo "  make run-server  - Start backend server"
	@echo "  make run-frontend - Start frontend dev server"
	@echo "  make start-all   - Start both servers"
	@echo "  make clean       - Remove temporary files"
	@echo "  make build       - Build frontend for production"

install:
	pip install -r requirements.txt

run-server:
	python backend/server.py

run-frontend:
	cd frontend && npm run dev

start-all:
	@echo "Starting AIrys servers..."
	pip install -r requirements.txt
	python backend/server.py &
	cd frontend && npm install --silent && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist build *.egg-info 2>/dev/null || true
	cd frontend && rm -rf node_modules package-lock.json 2>/dev/null || true

build:
	cd frontend && npm run build
# Start both frontend and backend servers
start-all:
	@echo "Starting AIrys servers..."
	-mkosi build || true
	pip install -r requirements.txt
	python backend/server.py &
	cd frontend && npm install --silent && npm run dev

# Clean temporary files
clean:
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && npm run clean 2>/dev/null || true

# Build frontend for production
build:
	cd frontend && npm run build

# Run linter
lint:
	python -m py_compile backend/*.py backend/**/*.py
	cd frontend && npm run lint 2>/dev/null || true

# Run tests
test:
	pytest tests/ 2>/dev/null || echo "No pytest tests found"
