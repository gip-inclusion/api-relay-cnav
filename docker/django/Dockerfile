ARG BASE_PYTHON_IMAGE="3.14-slim-trixie"
ARG UV_VERSION="0.11.21"

# Needed to be able to use UV_VERSION ARG
FROM ghcr.io/astral-sh/uv:${UV_VERSION} as uv_image

# ---- Builder Image ----
FROM python:${BASE_PYTHON_IMAGE} AS builder_image

COPY --from=uv_image /uv /bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---- Environnement ----

# ---- Installation des dépendances Python ----
WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv venv
RUN uv sync --frozen --no-dev


FROM python:${BASE_PYTHON_IMAGE} AS final_image

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHON_HISTORY /dev/null
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE="api_relay_cnav.settings"

COPY --from=builder_image /app /app
COPY docker/django/uwsgi.ini /app/uwsgi.ini
COPY docker/django/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN mkdir api_relay_cnav
COPY api_relay_cnav/ /app/api_relay_cnav/
RUN DJANGO_ENVIRONMENT=BUILD django-admin collectstatic --no-input

RUN useradd --shell /bin/bash --comment "Docker image user" api_relay_cnav

USER api_relay_cnav
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]


# ---- Dev Image ----
FROM final_image AS dev_image

USER root

ENV UV_CACHE_DIR=/app/.cache/uv

COPY --from=uv_image /uv /bin
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY Makefile manage.py /app/

# Install dev dependencies on top of the prod venv (image is built --no-dev)
RUN uv sync --frozen

# Let the runtime user write to /app (venv re-sync, collected static, etc.)
RUN chown -R api_relay_cnav: /app

USER api_relay_cnav
