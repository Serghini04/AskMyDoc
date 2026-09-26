SHELL := /bin/bash

# Uses .venv if present, otherwise falls back to venv.
VENV_DIR := venv
ifneq (,$(wildcard .venv/bin/python))
VENV_DIR := .venv
endif

PYTHON := $(VENV_DIR)/bin/python
UVICORN := $(VENV_DIR)/bin/uvicorn
ALEMBIC := $(VENV_DIR)/bin/alembic
COMPOSE := docker compose

.PHONY: help check-venv install up dev prod build rebuild down restart logs ps run migrate makemigration downgrade reindex test test-verbose lint format check

help:
	@echo "Available targets:"
	@echo "  make install                      - Install runtime + dev dependencies into the venv"
	@echo "  make dev                          - Start in dev mode (hot reload, bind mount)"
	@echo "  make prod                         - Start in prod mode (no bind mount, no reload)"
	@echo "  make up                           - Alias for dev"
	@echo "  make build                        - Rebuild Docker images (no cache)"
	@echo "  make rebuild                      - Stop, rebuild, and restart (prod)"
	@echo "  make down                         - Stop Docker containers"
	@echo "  make restart                      - Restart Docker containers"
	@echo "  make logs                         - Show Docker logs"
	@echo "  make ps                           - Show container status"
	@echo "  make run                          - Run FastAPI app locally (uvicorn)"
	@echo "  make test                         - Run tests (quiet)"
	@echo "  make test-verbose                 - Run tests (verbose)"
	@echo "  make lint                         - Lint and check formatting (ruff)"
	@echo "  make format                       - Auto-fix lint issues and format code (ruff)"
	@echo "  make check                        - lint + test (run before committing)"
	@echo "  make migrate                      - Apply DB migrations (upgrade head)"
	@echo "  make makemigration m=\"message\"    - Create auto migration"
	@echo "  make downgrade                    - Roll back one migration"
	@echo "  make reindex                      - Re-embed all documents (after changing EMBEDDING_MODEL)"

check-venv:
	@test -x "$(PYTHON)" || (echo "Virtualenv not found at $(VENV_DIR). Create it first." && exit 1)

# `python -m pip` works even if the venv was moved (its pip shebang would be stale).
install: check-venv
	$(PYTHON) -m pip install -r requirements-dev.txt

dev:
	$(COMPOSE) up -d

up: dev

prod:
	$(COMPOSE) -f docker-compose.yml up -d

build:
	$(COMPOSE) build --no-cache

rebuild: down build prod

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

run: check-venv
	$(UVICORN) app.main:app --host 0.0.0.0 --port $${PORT:-8000} --reload

test: check-venv
	$(PYTHON) -m pytest -q

test-verbose: check-venv
	$(PYTHON) -m pytest -vv

lint: check-venv
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format: check-venv
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

check: lint test

# Migrations run inside the api container so DATABASE_URL's "postgres" host
# resolves on the Docker network. The dev bind-mount means generated revision
# files land back in alembic/versions/ on the host.
migrate:
	$(COMPOSE) exec api alembic upgrade head

makemigration:
	@if [ -z "$(m)" ]; then \
		echo "Usage: make makemigration m=\"your migration message\""; \
		exit 1; \
	fi
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

downgrade:
	$(COMPOSE) exec api alembic downgrade -1

# Required after changing EMBEDDING_MODEL / EMBEDDING_DIMENSIONS.
reindex:
	$(COMPOSE) exec api python -m app.scripts.reindex
