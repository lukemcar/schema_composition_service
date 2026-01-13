.PHONY: \
	install install-dev \
	test test-unit test-integration \
	venv-clean \
	up down destroy clean \
	zip unzip

PYTHON       := python3
PIP          := $(PYTHON) -m pip
PYTEST       := $(PYTHON) -m pytest

PIP_FLAGS    := -e . -qq
PYTEST_FLAGS := -q

ZIP_NAME     := my_entity_service_python.zip


# ---------------------------------------------------------------------
# Install (editable)
# ---------------------------------------------------------------------
install:
	@echo ">>> Installing project (editable)..."
	@$(PIP) install $(PIP_FLAGS)

# Optional: install dev extras if you use them in pyproject.toml
install-dev:
	@echo ">>> Installing project (editable) with dev extras..."
	@$(PIP) install -e ".[dev]" -qq


compile: install
	@echo ">>> Compiling all python source files..."
	@$(PYTHON) -m compileall .



# ---------------------------------------------------------------------
# Python virtualenv reset
# ---------------------------------------------------------------------
venv-clean:
	@echo ">>> Removing existing virtual environment..."
	@rm -rf .venv

	@echo ">>> Creating new virtual environment..."
	@$(PYTHON) -m venv .venv

	@echo ">>> Bootstrapping pip, setuptools, wheel..."
	@. .venv/bin/activate && \
	python -m ensurepip --upgrade && \
	python -m pip install -U pip setuptools wheel -qq

	@echo ">>> Installing project in editable mode..."
	@. .venv/bin/activate && \
	python -m pip install -e . -qq

	@echo ">>> Virtual environment reset complete."


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

# Run all tests (unit + integration)
test: compile
	@echo ">>> Running all tests..."
	@$(PYTEST) $(PYTEST_FLAGS)

# Unit tests only (no Postgres, no Liquibase)
test-unit: compile
	@echo ">>> Running unit tests..."
	@$(PYTEST) $(PYTEST_FLAGS) -m "not postgres"

# Integration tests that hit Postgres via docker compose + Liquibase
test-integration: compile
	@echo ">>> Running integration tests..."
	@$(PYTEST) $(PYTEST_FLAGS) -m "postgres"


# ---------------------------------------------------------------------
# Docker dev stack
# ---------------------------------------------------------------------
up: compile
	@docker compose up --build

down:
	@docker compose down

destroy:
	@echo ">>> Destroying all containers and volumes..."
	@docker compose down -v

clean:
	@echo ">>> Pruning stopped containers..."
	@docker container prune -f

	@echo ">>> Pruning dangling images..."
	@docker image prune -f

	@echo ">>> Pruning unused networks..."
	@docker network prune -f

	@echo ">>> Pruning dangling volumes (safe: only unreferenced)..."
	@docker volume prune -f

	@echo ">>> Docker cleanup complete (safe mode)."


# ---------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------
zip:
	@echo ">>> Creating project archive: $(ZIP_NAME)"
	@rm -f $(ZIP_NAME)
	@zip -r $(ZIP_NAME) . \
		-x "*.zip" \
		-x ".venv/**" \
		-x "venv/**" \
		-x ".git/**" \
		-x "**/__pycache__/**" \
		-x "**/*.pyc" \
		-x "build/**" \
		-x "design/**" \
		-x "temp/**"

unzip:
	@echo ">>> Extracting project archive: $(ZIP_NAME)"
	@unzip -o $(ZIP_NAME) -d .

unzipl:
	@echo ">>> Listing project archive: $(ZIP_NAME)"
	@unzip -l $(ZIP_NAME)
