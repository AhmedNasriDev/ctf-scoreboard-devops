.DEFAULT_GOAL := help
# The first Python 3.11+ found on the PATH. Override with: make install PY=python3.12
PY      ?= $(shell for p in python3.12 python3.13 python3.11 python3; do \
             command -v $$p >/dev/null 2>&1 && $$p -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
             && { echo $$p; break; }; done)
VENV    ?= .venv
BIN     := $(VENV)/bin
HOSTP   ?= localhost:8000

.PHONY: help venv install run test cov lint fmt audit smoke big-csv clean distclean

help:  ## show this help
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
	 | sed 's/:.*##/\t/' | awk -F'\t' '{printf "  \033[1m%-10s\033[0m %s\n", $$1, $$2}'

venv:  ## create the virtual environment (needs Python 3.11 or later)
	@test -n "$(PY)" || { echo "No Python 3.11+ found. Install python3.12 (and python3.12-venv on Debian/Ubuntu)."; exit 1; }
	@test -d $(VENV) || $(PY) -m venv $(VENV) || { echo "venv failed: on Debian/Ubuntu install the matching pythonX.Y-venv package"; exit 1; }

install: venv  ## install runtime and development dependencies
	$(BIN)/pip install -q -U pip
	$(BIN)/pip install -q -r requirements-dev.txt
	$(BIN)/pip install -q -e .

run:  ## run the service (set ADMIN_TOKEN to enable the admin endpoints)
	$(BIN)/python -m scoreboard

test:  ## run the test suite
	$(BIN)/python -m pytest -q

cov:  ## run the test suite with a coverage report
	$(BIN)/python -m pytest -q --cov=src/scoreboard --cov-report=term-missing

lint:  ## check style and formatting (silent when clean)
	@$(BIN)/ruff check --quiet .
	@$(BIN)/ruff format --check --quiet .

fmt:  ## fix what can be fixed automatically
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

audit:  ## check the dependency manifest against the advisory database
	$(BIN)/pip-audit -r requirements.txt

smoke:  ## exercise a running instance: make smoke HOSTP=host:port
	./tools/smoke.sh $(HOSTP)

big-csv:  ## write big-teams.csv (> 1 MB), for the read-only /tmp experiment
	python3 tools/big_csv.py > big-teams.csv
	@ls -l big-teams.csv

clean:  ## remove caches and the local database
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info src/*.egg-info big-teams.csv
	find . -path ./$(VENV) -prune -o -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -f data/scoreboard.db

distclean: clean  ## also remove the virtual environment
	rm -rf $(VENV)
