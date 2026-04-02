SHELL := /bin/bash

# Uses .venv if present, otherwise falls back to venv.
VENV_DIR := venv
ifneq (,$(wildcard .venv/bin/python))
VENV_DIR := .venv
endif

PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn
ALEMBIC := $(VENV_DIR)/bin/alembic
COMPOSE := docker compose

.PHONY: help check-venv install up down restart logs ps run migrate makemigration downgrade

help:
	@echo "Available targets:"
	@echo "  make install                      - Install Python dependencies"
	@echo "  make up                           - Start Docker containers"
	@echo "  make down                         - Stop Docker containers"
	@echo "  make restart                      - Restart Docker containers"
	@echo "  make logs                         - Show Docker logs"
	@echo "  make ps                           - Show container status"
	@echo "  make run                          - Run FastAPI app (uvicorn)"
	@echo "  make migrate                      - Apply DB migrations (upgrade head)"
	@echo "  make makemigration m=\"message\"    - Create auto migration"
	@echo "  make downgrade                    - Roll back one migration"

check-venv:
	@test -x "$(PYTHON)" || (echo "Virtualenv not found at $(VENV_DIR). Create it first." && exit 1)

install: check-venv
	$(PIP) install -r requirements.txt

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

run: check-venv
	$(UVICORN) app.main:app --host 0.0.0.0 --port $${PORT:-8000} --reload

migrate: check-venv
	$(ALEMBIC) upgrade head

makemigration: check-venv
	@if [ -z "$(m)" ]; then \
		echo "Usage: make makemigration m=\"your migration message\""; \
		exit 1; \
	fi
	$(ALEMBIC) revision --autogenerate -m "$(m)"

downgrade: check-venv
	$(ALEMBIC) downgrade -1
