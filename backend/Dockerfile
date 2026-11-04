FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY pyproject.toml alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY seed ./seed
RUN pip install --no-cache-dir .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000"]
