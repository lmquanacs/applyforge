.PHONY: venv install dev test lint format run clean build help

help:
	@echo "CodeLens CLI - Available Commands:"
	@echo "  make venv     - Create virtual environment"
	@echo "  make install  - Install in production mode"
	@echo "  make dev      - Install with dev dependencies"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run flake8"
	@echo "  make format   - Format with black + isort"
	@echo "  make run      - Scan current directory"
	@echo "  make clean    - Remove build artifacts"

VENV=venv/bin

venv:
	python3 -m venv venv
	@echo "Activate with: source venv/bin/activate"

install:
	$(VENV)/pip install -e .

dev:
	$(VENV)/pip install -e ".[dev]"

test:
	$(VENV)/pytest tests/ -v --cov=codelens --cov-report=term

lint:
	$(VENV)/flake8 codelens/ --max-line-length=120

format:
	$(VENV)/black codelens/ tests/ --line-length=120
	$(VENV)/isort codelens/ tests/ --profile black

run:
	$(VENV)/codelens scan . --verbose

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean
	$(VENV)/python setup.py sdist bdist_wheel
