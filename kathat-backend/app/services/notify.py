"""Owner/team notification channels. Each function is a no-op if its env
vars aren't set, so the pipeline degrades gracefully channel by channel."""
import httpx

from ..config import settings


async def notify_slack(text: str) -> None:
    if not settings.slack_webhook_url:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(settings.slack_webhook_url, json={"text": text})
        except httpx.HTTPError as e:
            print(f"Slack notify failed: {e}")


async def notify_telegram_owner(text: str) -> None:
    if not (settings.telegram_bot_token and settings.telegram_owner_chat_id):
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={"chat_id": settings.telegram_owner_chat_id, "text": text})
        except httpx.HTTPError as e:
            print(f"Telegram notify failed: {e}")


async def log_to_notion(lead: dict) -> None:
    if not (settings.notion_api_key and settings.notion_database_id):
        return
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    body = {
        "parent": {"database_id": settings.notion_database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": lead.get("name") or lead.get("email") or lead.get("id", "")}}]},
            "Stage": {"select": {"name": lead.get("temperature", "cold")}},
            "Score": {"number": lead.get("score", 0)},
            "Page": {"rich_text": [{"text": {"content": lead.get("source_page") or ""}}]},
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json=body, headers=headers)
        except httpx.HTTPError as e:
            print(f"Notion log failed: {e}")


async def sync_external_crm(lead: dict) -> None:
    if not settings.crm_webhook_url:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(settings.crm_webhook_url, json=lead)
        except httpx.HTTPError as e:
            print(f"External CRM sync failed: {e}")
