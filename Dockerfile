# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HUNTER_DB_PATH=/app/.data/hunter.sqlite3
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt && useradd --create-home hunter && mkdir /app/.data && chown hunter:hunter /app/.data
COPY --chown=hunter:hunter hunter ./hunter
COPY --chown=hunter:hunter web ./web
USER hunter
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"
CMD ["python", "-m", "uvicorn", "hunter.app:app", "--no-proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
