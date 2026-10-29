# Operations and release gates

This is a development-stage single-instance application. A container configuration is supplied; public hosting, TLS, live providers and external notifications require separate runtime configuration and validation. Do not declare production readiness from a local test run.

## Local setup

From repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pytest -q
AOH_DB_PATH=var/opportunity.db .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use a distinct database for development and production. Never commit the database or session data. Bind to loopback for local development. The container sets secure cookies; an HTTPS terminating proxy is necessary to use authenticated pages in deployment. Production must use a durable mounted `/data`, one application instance and one worker until concurrency/load acceptance is complete.

## Container

```bash
docker build -t opportunity-hunter:RELEASE .
docker volume create opportunity-data
docker run --rm --name opportunity-hunter -p 127.0.0.1:8000:8000 -v opportunity-data:/data opportunity-hunter:RELEASE
```

Replace RELEASE with an immutable release identifier. The health check reads `/healthz`; a healthy response alone does not validate login, policy or provider operations. Browser smoke and persistence checks are also release gates. Docker commands are a procedure, not evidence that this environment has built or run them.

## Backup and restore

Use SQLite's online backup API against the configured database; do not copy only the live main file while WAL writes may be active. Store backups outside the checkout with restrictive permissions and encryption/access controls provided by the hosting platform.

```python
import sqlite3
with sqlite3.connect('/data/opportunity.db') as source:
    with sqlite3.connect('/secure-backup/opportunity.db') as destination:
        source.backup(destination)
        assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
```

Verify restore into a separate environment, check row counts/relationships and representative authenticated workflows. Never print PII or session tokens in a restore report. Stop writers before replacing a production database. Backups contain personal data and require the same retention/deletion policy as primary storage.

## Rollback

Retain the previous image and a verified pre-migration backup. Stop the service, restore a compatible database if schema changed, start the previous image, then verify health and a representative workflow. Forward-only schema changes require a tested data rollback plan. No production rollback has been exercised by merely writing this procedure.

## Remaining operational acceptance

- Hosting account, domain/TLS and secrets supplied through deployment settings.
- Pinned dependency vulnerability review and reproducible transitive dependency lock.
- Remote CI execution observed, container build/run and deployment smoke verified.
- Persistent migrations, backup/restore and rollback rehearsed on deployment infrastructure.
- External integrations tested with authorized accounts, bounded retries and alerts.
- Auth abuse controls, password recovery/email verification, privacy deletion/export and retention validated.
- Load/concurrency measurements and monitoring/alert delivery verified.
