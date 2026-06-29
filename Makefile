.PHONY: build lint format typecheck test

build: lint format typecheck test
	poetry build

lint:
	poetry run ruff check src tests examples

format:
	poetry run ruff format src tests examples

typecheck:
	poetry run pyright

test:
	poetry run pytest
