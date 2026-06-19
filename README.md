# API Relay CNAV

API de relay pour interroger la CNAV.

## Développement local

# Prérequis
python >= 3.14
docker + docker-compose
uv

# Installation
```bash
make venv
source .venv/bin/activate
```

# Lancer les services
```bash
docker-compose up
make runserver
```

# Tests
```bash
make test
make quality
```
