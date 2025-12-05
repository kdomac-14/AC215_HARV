FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml ./
COPY backend ./backend

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system .

COPY models ./models

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
