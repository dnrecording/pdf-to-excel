.PHONY: help install test coverage lint format clean gui build

.DEFAULT_GOAL := help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run all tests
	source .venv/bin/activate && pytest tests/ -v

coverage: ## Run tests with coverage report
	source .venv/bin/activate && pytest tests/ --cov=pdf_to_excel --cov-report=term-missing --cov-report=html

lint: ## Check code style
	flake8 pdf_to_excel/ tests/

format: ## Format code with black
	black pdf_to_excel/ tests/

clean: ## Remove generated files
	rm -rf .pytest_cache .coverage htmlcov __pycache__ *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

gui: ## Launch GUI application
	source .venv/bin/activate && python gui_launcher.py

build: ## Build standalone application (.app for macOS)
	./build_app.sh
