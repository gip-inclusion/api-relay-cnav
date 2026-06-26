#!/bin/bash
set -e

if [[ "$DJANGO_ENVIRONMENT" == "DEV" ]]; then
	uv sync --frozen
	python manage.py migrate
	exec python manage.py runserver 0.0.0.0:8000
else
	exec uwsgi --ini /app/uwsgi.ini
fi
