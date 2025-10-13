FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && . .venv/bin/activate && uv pip install -e .
COPY src ./src
ENV PYTHONUNBUFFERED=1
