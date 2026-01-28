.PHONY: venv install test smoke lint typecheck perf up down rebuild verify allure

PYTHON ?= python3.11

venv:
	$(PYTHON) -m venv .venv

install:
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && python -m pip install -r requirements-dev.txt

test:
	. .venv/bin/activate && python -m pytest

smoke:
	. .venv/bin/activate && python -m pytest -m smoke

up:
	docker compose up -d --build

down:
	docker compose down

rebuild:
	docker compose down
	docker compose up -d --build

lint:
	. .venv/bin/activate && python -m ruff check .

typecheck:
	. .venv/bin/activate && python -m mypy api/app tests

perf:
	. .venv/bin/activate && python -m pip install -r perf/requirements.txt
	. .venv/bin/activate && LOCUST_HOST=http://localhost:8000 python -m locust -f perf/locustfile.py --headless -u 10 -r 2 -t 10s --csv=perf/results

allure:
	. .venv/bin/activate && python -m pytest --alluredir=allure-results
	allure generate allure-results -o allure-report --clean

verify:
	$(MAKE) smoke
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) perf
