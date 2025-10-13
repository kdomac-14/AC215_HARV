FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv venv && . .venv/bin/activate && uv pip install -e .
COPY app ./app
ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
