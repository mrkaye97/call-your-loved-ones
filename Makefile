.PHONY: format lint type check install

install:
	poetry install --with dev --no-root

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run ruff check .

type:
	poetry run mypy .

check: lint type
	@echo "All checks passed!"

fix:
	poetry run ruff check --fix .
	poetry run black .
	poetry run isort .
