FROM python:3.11-slim

WORKDIR /app

# System deps for ifcopenshell
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY bimoryn/ ./bimoryn/
COPY samples/ ./samples/

RUN pip install --no-cache-dir ".[dev]"

# Smoke-test the CLI is importable
RUN python -c "from bimoryn.engine import Engine"

ENTRYPOINT ["bimoryn"]
