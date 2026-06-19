PGDATABASE ?= api_relay_cnav
UV_LOCK ?= uv.lock
VIRTUAL_ENV ?= .venv
DJANGO_ENVIRONMENT ?= DEV

export DJANGO_ENVIRONMENT := $(DJANGO_ENVIRONMENT)
export PATH := $(VIRTUAL_ENV)/bin:$(PATH)

.PHONY: runserver venv quality fix

runserver: $(VIRTUAL_ENV)
	python manage.py runserver $(RUNSERVER_DOMAIN)

$(VIRTUAL_ENV): $(UV_LOCK)
	uv venv
	uv sync --frozen
	touch $@

venv: $(VIRTUAL_ENV)

quality: $(VIRTUAL_ENV)
	ruff check .
	ruff format --check .
	python manage.py makemigrations --check --dry-run --noinput || (echo "⚠ Missing migration ⚠"; exit 1)
	python manage.py collectstatic --no-input

fix: $(VIRTUAL_ENV)
	ruff check --fix .
	ruff format .

test: $(VIRTUAL_ENV)
	pytest --numprocesses=logical --create-db

.PHONY: resetdb
resetdb:
	dropdb --if-exists $(PGDATABASE)
	createdb $(PGDATABASE)
	python manage.py migrate
