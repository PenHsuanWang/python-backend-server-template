FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml README.md requirements.lock ./
COPY src ./src
COPY bootstrap ./bootstrap
COPY server.py worker.py manage.py ./
RUN python -m pip install --constraint requirements.lock .

USER app
EXPOSE 8000
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
