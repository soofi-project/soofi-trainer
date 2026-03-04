.PHONY: help test test-unit test-integration test-e2e test-cov lint format clean

help:
	@echo "Available targets:"
	@echo "  test             - Run all tests"
	@echo "  test-unit        - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-e2e         - Run only e2e tests"
	@echo "  test-cov         - Run tests with coverage report"
	@echo "  lint             - Run ruff linter"
	@echo "  format           - Format code with black"
	@echo "  clean            - Remove test artifacts"

test:
	pytest tests/

test-unit:
	pytest tests/ -m unit

test-integration:
	pytest tests/ -m integration

test-e2e:
	pytest tests/ -m e2e

test-cov:
	pytest tests/ --cov=src/training_gateway --cov-report=term --cov-report=html

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
	rm -rf .pytest_cache __pycache__ .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
