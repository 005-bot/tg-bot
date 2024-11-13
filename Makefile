# Makefile for the web scraping project using Pipenv

# Variables
DOCKER_COMPOSE = docker-compose
PIPENV = pipenv

# Docker commands
build:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

# Pipenv commands
install:
	$(PIPENV) install

install-dev:
	$(PIPENV) install --dev

shell:
	$(PIPENV) shell

test:
	$(PIPENV) run pytest tests/

lint:
	$(PIPENV) run flake8 app/ tests/

format:
	$(PIPENV) run black app/ tests/

# Development commands
run-local:
	$(PIPENV) run python -m app

ngrok:
	ngrok http 8000

# Cleanup
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete

# Help command
help:
	@echo "Available commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start Docker containers"
	@echo "  make down          - Stop Docker containers"
	@echo "  make logs          - View Docker container logs"
	@echo "  make install       - Install Python dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make shell         - Spawn a shell within the virtualenv"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code with Black"
	@echo "  make run-local     - Run the application locally"
	@echo "  make clean         - Remove Python cache files"

.PHONY: build up down logs install install-dev shell test lint format run-local clean help
