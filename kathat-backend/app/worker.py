"""
Background work — now run via FastAPI's BackgroundTasks (in-process, after
the response is sent) rather than a separate Redis/RQ worker. This keeps
the whole backend deployable as a single process with a single SQLite file:
no Redis, no second container, no message broker to operate.

Trade-off, stated plainly: BackgroundTasks run in the same process as the
API. If you outgrow a single instance (multiple API replicas, need retries/
durability for jobs), swap this for a real queue (RQ+Redis, Celery, etc.) —
the functions below are already isolated and would move over unchanged.
"""
from .database import SessionLocal
from .models import Lead, Event
from .services import notify, whatsapp, sheets_sync
from .services.ai_fallback import generate_with_fallback


async def process_lead_stage_change(lead_id: str, temperature: str) -> None:
    db = SessionLocal()
    try:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        lead_dict = {
            "id": lead.id, "name": lead.name, "email": lead.email, "phone": lead.phone,
            "score": lead.score, "temperature": lead.temperature,
            "source_page": lead.source_page,
        }

        # Always: sync to the CRM + Notion the moment a lead is worth a look
        await notify.sync_external_crm(lead_dict)
        await notify.log_to_notion(lead_dict)

        if temperature in ("warm", "hot"):
            # Optional Google Sheets mirror — a human-friendly view, not the
            # database. No-ops silently if not configured.
            await sheets_sync.append_lead_row(lead_dict)

        if temperature != "hot":
            return

        journey = (
            db.query(Event)
            .filter(Event.visitor_id == lead.visitor_id)
            .order_by(Event.created_at)
            .all()
        )
        pages = " -> ".join(e.page for e in journey if e.page) or (lead.source_page or "the site")

        summary = await generate_with_fallback(
            messages=[{
                "role": "user",
                "content": (
                    f"A website visitor's journey: {pages}. In one sentence, summarize what "
                    "they're most likely trying to buy, written for a sales rep."
                ),
            }]
        )

        await notify.notify_slack(
            f"\U0001F525 *Hot lead*\n*Contact:* {lead.email or lead.phone or 'anonymous'}\n"
            f"*Page:* {lead.source_page}\n*Score:* {lead.score}\n*AI read:* {summary or 'n/a'}"
        )
        await notify.notify_telegram_owner(
            f"\U0001F525 Hot lead: {lead.email or lead.phone or 'anonymous'} on {lead.source_page} (score {lead.score})"
        )

        # Backend-triggered WhatsApp message to the LEAD — the only way
        # WhatsApp gets involved. No chat-button widget anywhere in the UI.
        if lead.phone:
            await whatsapp.send_template(lead.phone)
    finally:
        db.close()


async def summarize_conversation(conversation_id: str) -> None:
    from .models import Conversation, Message

    db = SessionLocal()
    try:
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            return
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )
        transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)
        summary = await generate_with_fallback(messages=[{
            "role": "user",
            "content": f"Summarize this sales conversation in 1-2 sentences for a CRM note:\n\n{transcript}",
        }])
        conversation.summary = summary
        db.commit()
    finally:
        db.close()
