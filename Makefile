.PHONY: build lint format typecheck test check-git check-version publish

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

check-git:
	@if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "Error: uncommitted changes — commit or stash before publishing"; exit 1; \
	fi
	@VERSION=$$(poetry version -s); TAG="v$$VERSION"; \
	if ! git tag | grep -qx "$$TAG"; then \
		echo "Error: tag $$TAG not found — run: git tag $$TAG"; exit 1; \
	fi
	@VERSION=$$(poetry version -s); TAG="v$$VERSION"; \
	if ! git describe --exact-match --tags HEAD 2>/dev/null | grep -qx "$$TAG"; then \
		echo "Error: HEAD is not at tag $$TAG — commits exist after tagging"; exit 1; \
	fi
	@echo "Git OK: clean tree, HEAD tagged as v$$(poetry version -s)"

check-version:
	@VERSION=$$(poetry version -s); \
	if curl -sf "https://pypi.org/pypi/fastapi-concurrency-limiter/$$VERSION/json" > /dev/null; then \
		echo "Error: v$$VERSION already exists on PyPI"; exit 1; \
	fi
	@echo "PyPI OK: v$$(poetry version -s) is available"

publish: check-git check-version build
	poetry publish