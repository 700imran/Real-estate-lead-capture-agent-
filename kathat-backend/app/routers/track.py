from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Visitor, Event, Lead, VisitorSession
from ..schemas import TrackPayload, TrackResponse
from ..services.scoring import score_events, classify, repeat_visitor_bonus
from ..worker import process_lead_stage_change
from .ws import manager

router = APIRouter()


def _track_session(db: Session, visitor_id: str, session_id: str | None) -> int:
    """Insert-if-new (visitor_id, session_id) row, return the visitor's
    total distinct-session count. SQLite-backed — no Redis needed."""
    if not session_id:
        return 1
    exists = (
        db.query(VisitorSession)
        .filter(VisitorSession.visitor_id == visitor_id, VisitorSession.session_id == session_id)
        .first()
    )
    if not exists:
        db.add(VisitorSession(visitor_id=visitor_id, session_id=session_id))
        try:
            db.flush()
        except IntegrityError:
            db.rollback()  # lost a race with another request for the same session — fine, just count
    return db.query(func.count(VisitorSession.id)).filter(VisitorSession.visitor_id == visitor_id).scalar() or 1


@router.post("/track", response_model=TrackResponse)
async def track(payload: TrackPayload, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    visitor = db.get(Visitor, payload.visitor_id)
    if not visitor:
        visitor = Visitor(id=payload.visitor_id, session_count=1, is_repeat=False)
        db.add(visitor)
        db.flush()

    session_count = _track_session(db, visitor.id, payload.session_id)
    visitor.session_count = session_count
    visitor.is_repeat = session_count > 1

    for e in payload.events:
        db.add(Event(visitor_id=visitor.id, type=e.type, page=e.page or payload.current_page, data=e.data))

    lead = db.query(Lead).filter(Lead.visitor_id == visitor.id).one_or_none()
    if not lead:
        # Set score/temperature explicitly rather than relying on the
        # column default — that default only applies at flush/INSERT time,
        # and we read lead.score below before this row is flushed.
        lead = Lead(visitor_id=visitor.id, source_page=payload.current_page, score=0, temperature="cold")
        db.add(lead)

    if payload.email:
        lead.email = payload.email
    if payload.phone:
        lead.phone = payload.phone
    if payload.current_page:
        lead.source_page = lead.source_page or payload.current_page

    prev_temperature = lead.temperature
    incoming = score_events([e.model_dump() for e in payload.events], payload.current_page)
    lead.score = lead.score + incoming + (repeat_visitor_bonus(session_count) if incoming else 0)
    lead.temperature = classify(lead.score)

    db.commit()
    db.refresh(lead)

    # Live dashboard feed — fire and forget, doesn't block the response
    await manager.broadcast({
        "type": "lead_activity",
        "lead_id": lead.id,
        "score": lead.score,
        "temperature": lead.temperature,
        "page": payload.current_page,
    })

    # Crossed into warm/hot for the first time -> hand off to a background
    # task (CRM sync, Notion log, Sheets mirror, and for hot leads: Slack +
    # Telegram + WhatsApp + an AI-written sales summary). Runs after this
    # response is sent, so a slow WhatsApp/LLM call never adds latency to
    # the visitor's page.
    if lead.temperature != prev_temperature and lead.temperature in ("warm", "hot"):
        background_tasks.add_task(process_lead_stage_change, lead.id, lead.temperature)

    return TrackResponse(status="ok", score=lead.score, temperature=lead.temperature)
