FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HUNTER_DB_PATH=/app/.data/hunter.sqlite3
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home hunter && mkdir /app/.data && chown hunter:hunter /app/.data
COPY hunter ./hunter
COPY web ./web
USER hunter
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"
CMD ["python", "-m", "uvicorn", "hunter.app:app", "--host", "0.0.0.0", "--port", "8000"]
