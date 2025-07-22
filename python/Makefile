.PHONY: install format lint typecheck test test-watch coverage all clean

# Install dependencies
install:
	pip install -r requirements.txt

# Format code
format:
	black .
	isort .

# Lint code
lint:
	ruff check .

# Type check
typecheck:
	mypy .

# Run tests
test:
	pytest

# Run tests in watch mode
test-watch:
	pytest-watch

# Run tests with coverage
coverage:
	pytest --cov=. --cov-report=html --cov-report=term

# Run all quality checks
all: format lint typecheck test

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage