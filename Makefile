.DEFAULT_GOAL := help

PY      ?= python
PIP     ?= $(PY) -m pip
VENV    ?= .venv
BIN     := $(VENV)/bin
ACT     := . $(BIN)/activate

# ----------------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------------

.PHONY: venv
venv: ## Create local virtualenv
	$(PY) -m venv $(VENV)

.PHONY: install
install: ## Install runtime dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

.PHONY: install-dev
install-dev: ## Install dev + runtime dependencies
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

# ----------------------------------------------------------------------------
# Quality
# ----------------------------------------------------------------------------

.PHONY: lint
lint: ## Run ruff
	ruff check infra tests

.PHONY: format
format: ## Auto-format with black + ruff --fix
	black infra tests
	ruff check --fix infra tests

.PHONY: typecheck
typecheck: ## Run mypy
	mypy infra

.PHONY: test
test: ## Run the test suite
	pytest --cov=infra --cov-report=term-missing

.PHONY: check
check: lint typecheck test ## Run all CI checks locally

# ----------------------------------------------------------------------------
# Infra shortcuts (thin wrappers around the CLI)
# ----------------------------------------------------------------------------

.PHONY: up harden deploy status destroy
up:       ; infra up
harden:   ; infra harden
deploy:   ; infra deploy
status:   ; infra status
destroy:  ; infra destroy

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
