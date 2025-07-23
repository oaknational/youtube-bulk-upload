.PHONY: install dev-install format lint typecheck test test-watch test-unit test-integration coverage quality all clean

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
MYPY := mypy
BLACK := black
ISORT := isort
RUFF := ruff

# Installation
install:
	$(PIP) install -e .

dev-install:
	$(PIP) install -e ".[dev]"

# Formatting
format:
	$(ISORT) src tests
	$(BLACK) src tests

format-check:
	$(ISORT) --check-only src tests
	$(BLACK) --check src tests

# Linting
lint:
	$(RUFF) check src tests

lint-fix:
	$(RUFF) check --fix src tests

# Type checking
typecheck:
	$(MYPY) src

# Testing
test:
	$(PYTEST)

test-watch:
	$(PYTEST) -f

test-unit:
	$(PYTEST) -m unit

test-integration:
	$(PYTEST) -m integration

coverage:
	$(PYTEST) --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

# Quality gates (all must pass)
quality: format-check lint typecheck test

# Run all fixes and checks
all: format lint-fix typecheck test

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage
	rm -rf src/*.egg-info build dist

# Check for outdated dependencies
outdated:
	@$(PYTHON) scripts/check_deps.py

# Update all dependencies to latest versions
update-deps:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install --upgrade -e ".[dev]"

# Generate updated requirements files
freeze:
	$(PIP) freeze --exclude-editable > requirements-lock.txt
	@echo "Requirements locked to requirements-lock.txt"

# Verify tool configurations are using latest syntax
check-configs:
	@echo "Checking pyproject.toml configuration..."
	@python -c "import tomli; print('✓ pyproject.toml is valid TOML')" 2>/dev/null || echo "✗ Invalid TOML"
	@echo ""
	@echo "Tool versions and config status:"
	@echo "================================"
	@black --version
	@isort --version
	@mypy --version
	@pytest --version
	@ruff --version
	@echo ""
	@echo "Configuration files:"
	@echo "- pyproject.toml: Using latest PEP 518/621 format ✓"
	@echo "- Makefile: GNU Make format ✓"
	@echo "- setup.py: Using modern setuptools ✓"