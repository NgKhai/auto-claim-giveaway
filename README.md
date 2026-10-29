# Autonomous Opportunity Hunter

A development-stage workspace for discovering opportunity leads, inspecting evidence and tracking next steps under explicit user control.

## Current capability

Create an account, save goals, search a clearly labeled research catalog, inspect source evidence, record eligibility decisions, track/recheck/cancel leads, change profile preferences and delete your account. Sessions, CSRF protection, account isolation and audit records are enforced server-side.

The initial catalog contains reference sources, **not verified active offers**. Tracking creates a local record, not a provider registration. Live discovery, semantic matching, approved browser execution and external notifications are tracked in the [roadmap](docs/product/ROADMAP.md). This is not a production-ready release.

## Run locally

Requires Python 3.12+.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open the local server in your browser and create a development account. No preconfigured account or external API key is needed for the research catalog. Use synthetic data for development.

| Setting | Purpose |
| --- | --- |
| `AOH_DB_PATH` | SQLite file path; default `var/opportunities.db` |
| `AOH_SECURE_COOKIES` | Enable secure cookies for HTTPS deployments |

The `/healthz` endpoint checks database access. Containers require a persistent `/data` volume; production requires HTTPS and secure cookies. See [operations](docs/architecture/OPERATIONS.md) for container setup, backup and rollback procedures.

## Documentation

- [Research and source references](docs/README.md)
- [Product requirements](docs/product/PRD.md) and [system requirements](docs/product/SRS.md)
- [Architecture decision](docs/architecture/ADR-001-modular-monolith.md)
- [HTTP contracts](docs/product/API.md)
- [Roadmap](docs/product/ROADMAP.md) and [test plan](docs/quality/TEST_PLAN.md)

User content and website text must never grant execution permissions. No CAPTCHA bypass, sensitive-data auto-submission or unreviewed generated executor code is permitted.
