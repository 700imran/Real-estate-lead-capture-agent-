# Kathat Estate — Backend

FastAPI + SQLite. This is the part that needs an install/build step
(`pip install`) — paired with the separately-deployed, zero-build
`kathat-frontend/`.

## What this is

Visitor tracking ingestion, lead scoring, a small CRM, an AI sales agent
(GPT-4o → Claude fallback), and backend-triggered notifications (WhatsApp
Business Cloud API, Telegram, Slack, Notion) — plus a JWT-protected API
for the admin dashboard the frontend calls.

## Run it

```bash
pip install -r requirements.txt
export SECRET_KEY="change-me-to-something-random"
export CORS_ORIGINS="https://your-frontend-domain.com"   # wherever kathat-frontend/ ends up
python -m app.seed          # creates data/are.db, pipeline stages, admin user
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

That's it — one process, one SQLite file (`data/are.db`). No Postgres, no
Redis, no message broker to run alongside it.

First login for the dashboard: `admin@example.com` / `changeme123` by
default (override with `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` env vars
before seeding) — **change this password immediately** in anything beyond
local testing.

## Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

Mount `/app/data` as a volume so the SQLite file survives container
restarts. Works on any container host with a free tier — Render, Railway,
Fly.io, a $0 VPS — since there's no second service (database, queue
worker) to also provision.

## CORS — the one setting that matters for the split

Since the frontend is a separate static deployment on its own domain, set
`CORS_ORIGINS` to that exact domain (comma-separate multiple if you have a
staging + production frontend):

```bash
CORS_ORIGINS=https://kathatestate.com,https://staging.kathatestate.com
```

Without this, the browser will block the frontend's requests even though
the backend itself is running fine.

## Environment variables

All optional except `SECRET_KEY` and `CORS_ORIGINS` — everything else
degrades gracefully (that integration just stays silent) if left unset:

| Variable | For |
|---|---|
| `SECRET_KEY` | JWT signing — set this to something random |
| `CORS_ORIGINS` | Allow the frontend's domain to call this API |
| `DATABASE_URL` | Defaults to `sqlite:///./data/are.db` — change only if moving to Postgres |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | AI sales agent + hot-lead summaries |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_TEMPLATE_NAME` | Backend-triggered WhatsApp (Meta Cloud API) |
| `SLACK_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID` | Owner alerts |
| `NOTION_API_KEY`, `NOTION_DATABASE_ID` | CRM log to Notion |
| `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID` | Optional Google Sheets lead mirror (see `app/services/sheets_sync.py`) |
| `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` | First dashboard login, set before running `app.seed` |

## API surface the frontend depends on

- `POST /api/v1/track` — pixel event ingestion (public, no auth)
- `POST /api/v1/agent/chat` — AI sales agent (public, no auth)
- `POST /api/v1/auth/login` — dashboard login, returns a JWT
- `GET /api/v1/leads`, `GET /api/v1/leads/stats` — dashboard data (JWT required)
- `WS /api/v1/ws/dashboard` — live dashboard feed (JWT not enforced on the
  socket itself today — put this behind your reverse proxy / firewall if
  that matters for your deployment, or add a token check to `routers/ws.py`)
- `GET /docs` — full interactive API reference (Swagger UI)

## No signup for the public-facing parts

`/track` and `/agent/chat` — the two endpoints the public site actually
calls — require no authentication by design, matching the frontend's
open-to-everyone requirement. Only the dashboard-facing endpoints
(`/leads`, `/leads/stats`) require a login.
