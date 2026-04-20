# lumina-forge — task runner
# https://github.com/casey/just

set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# Default: list available recipes
default:
    @just --list

# --- Setup ------------------------------------------------------------------

# Install Python + Node dependencies
setup: setup-py setup-node

# Install Python deps via uv (workspace-aware)
setup-py:
    uv sync --all-packages

# Install Node deps via pnpm
setup-node:
    pnpm install

# --- Develop ----------------------------------------------------------------

# Run the desktop app in dev mode (expects `just api` running in another shell).
dev:
    cd app && pnpm tauri dev

# Same, but Vite only (faster iteration on UI, no native window)
dev-web:
    cd app && pnpm dev

# Type-check and production-build the web bundle
build-web:
    cd app && pnpm build

# Run the scraper against all known sources (defaults: fextralife, every type)
scrape *FLAGS:
    uv run scraper {{FLAGS}}

# Scrape a subset — alias kept handy for quick debugging
scrape-pictos:
    uv run scraper --source fextralife --type picto

# Run the optimizer CLI against a JSON inventory
optimize inventory="examples/gustave-basic.json" *FLAGS:
    uv run optimizer --inventory {{inventory}} {{FLAGS}}

# Start the local HTTP API (FastAPI + uvicorn)
api *FLAGS:
    uv run lumina-forge-api {{FLAGS}}

# --- Quality ----------------------------------------------------------------

# Run Python tests
test:
    uv run pytest

# Type-check with mypy
typecheck:
    uv run mypy packages/scraper packages/optimizer

# Lint with ruff
lint:
    uv run ruff check .

# Auto-format with ruff
format:
    uv run ruff format .

# Run everything CI would run
check: lint typecheck test

# --- Release ----------------------------------------------------------------

# Build the desktop app in release mode (Phase 4)
build:
    @echo "TODO — release build lands in Phase 4"

# --- Housekeeping -----------------------------------------------------------

# Remove caches and generated artifacts
clean:
    uv cache clean
    pnpm store prune
