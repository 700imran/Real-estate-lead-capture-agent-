"""
WhatsApp integration — Meta WhatsApp Business Cloud API, called only from the
server. There is intentionally no wa.me / click-to-chat button anywhere in
this system: the visitor never has to click through to WhatsApp themselves.
The backend decides, based on the scored lead event, when a message goes out
and sends it directly via the Graph API.

Two message paths:
  - Template messages (send_template): required for the first outbound
    message to a lead outside a live conversation window — Meta requires a
    pre-approved template for this. Use for the initial "hot lead" ping.
  - Session messages (send_session_text): free-form text, only usable while
    a 24h customer-initiated session is open (i.e. the lead messaged first).

If WHATSAPP_TOKEN / WHATSAPP_PHONE_ID aren't configured, both functions are
no-ops — the rest of the pipeline (CRM, dashboard, Slack) still works.
"""
import httpx

from ..config import settings

GRAPH_BASE = "https://graph.facebook.com/v20.0"


async def send_template(to_phone: str, template_name: str | None = None, language: str = "en_US") -> dict | None:
    if not (settings.whatsapp_token and settings.whatsapp_phone_id and to_phone):
        return None
    url = f"{GRAPH_BASE}/{settings.whatsapp_phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name or settings.whatsapp_template_name,
            "language": {"code": language},
        },
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            print(f"WhatsApp template send failed: {e}")
            return None


async def send_session_text(to_phone: str, body: str) -> dict | None:
    if not (settings.whatsapp_token and settings.whatsapp_phone_id and to_phone):
        return None
    url = f"{GRAPH_BASE}/{settings.whatsapp_phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": body},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            print(f"WhatsApp session send failed: {e}")
            return None
