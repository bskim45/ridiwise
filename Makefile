VENV := ./.venv/bin

.PHONY: install
install:
	rye sync
	$(VENV)/pre-commit install
	$(VENV)/playwright install chromium

.PHONY: lint
lint:
	$(VENV)/ruff check src
	$(VENV)/pylint src

.PHONY: lint-fix
lint-fix:
	$(VENV)/ruff check --fix src

.PHONY: format
format:
# sort imports
	$(VENV)/ruff check --select I --fix src
# format code
	$(VENV)/ruff format --diff src || true
	$(VENV)/ruff format src

.PHONY: test
test:
	$(VENV)/pytest \
		--cov-report term-missing:skip-covered \
		--cov-report html \
		--cov-report xml \
		-vvv \
		tests
		| tee pytest-coverage.txt

clean:
	rm -rf htmlcov pytest-coverage.txt

%:
	@:
