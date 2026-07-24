"""
Centralized settings. Everything is read from the environment so the same
image runs unchanged across local / staging / production — only the .env
(or the orchestrator's secret store) changes.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    env: str = "development"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12

    # Datastore — SQLite by default: zero setup, one file, genuinely free
    # anywhere. Swap database_url for a Postgres URL later if you outgrow
    # single-file storage; nothing else in the app assumes SQLite.
    database_url: str = "sqlite:///./data/are.db"

    # CORS — the Next.js origin(s) allowed to call this API
    cors_origins: str = "http://localhost:3000"

    # AI providers (fallback chain: OpenAI -> Anthropic)
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # WhatsApp Business Cloud API (Meta) — backend-triggered sends only.
    # There is deliberately no click-to-chat widget anywhere in this system;
    # every WhatsApp message originates from the server in reaction to a
    # scored lead event.
    whatsapp_token: str | None = None
    whatsapp_phone_id: str | None = None
    whatsapp_template_name: str = "lead_followup"

    # Owner-facing notifications
    slack_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_owner_chat_id: str | None = None
    notion_api_key: str | None = None
    notion_database_id: str | None = None
    crm_webhook_url: str | None = None

    # Optional: mirror warm/hot leads into a Google Sheet for anyone who
    # wants a spreadsheet view. This is a one-way export, not the database —
    # see services/sheets_sync.py. Leave blank to skip entirely.
    google_service_account_json: str | None = None  # path to the service account key file
    google_sheet_id: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
