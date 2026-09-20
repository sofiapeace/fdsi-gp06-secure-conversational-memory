FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"

COPY experiments ./experiments
COPY tests ./tests
COPY Makefile ./

ENV PY=python
CMD ["python", "-m", "memlab.cli", "info"]
