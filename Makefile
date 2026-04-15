.PHONY: setup test lint clean

setup:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -e .
	@[ -f .env ] || cp .env.example .env && echo "Created .env from .env.example"
	@echo "\nDone! Activate your environment with: source venv/bin/activate"

test:
	venv/bin/pytest tests/ -v

lint:
	venv/bin/black career_ai/ tests/
	venv/bin/flake8 career_ai/ tests/
	venv/bin/mypy career_ai/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info
