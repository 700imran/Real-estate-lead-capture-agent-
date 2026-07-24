from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import Lead, Note, Tag, Visitor, PipelineStage, User, AuditLog
from ..schemas import LeadOut, LeadUpdate, NoteCreate, NoteOut, TagAssign

router = APIRouter()


@router.get("/leads", response_model=list[LeadOut])
def list_leads(
    temperature: str | None = None,
    owner_id: str | None = None,
    pipeline_stage_id: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(Lead)
    if temperature:
        q = q.filter(Lead.temperature == temperature)
    if owner_id:
        q = q.filter(Lead.owner_id == owner_id)
    if pipeline_stage_id:
        q = q.filter(Lead.pipeline_stage_id == pipeline_stage_id)
    return q.order_by(Lead.score.desc()).limit(200).all()


@router.get("/leads/stats")
def lead_stats(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    live_visitors = db.query(Visitor).filter(Visitor.last_seen >= five_min_ago).count()
    qualified_leads = db.query(Lead).filter(Lead.temperature.in_(["warm", "hot"])).count()

    funnel = (
        db.query(PipelineStage.name, func.count(Lead.id))
        .outerjoin(Lead, Lead.pipeline_stage_id == PipelineStage.id)
        .group_by(PipelineStage.id, PipelineStage.name, PipelineStage.position)
        .order_by(PipelineStage.position)
        .all()
    )
    by_owner = (
        db.query(User.name, func.count(Lead.id))
        .join(Lead, Lead.owner_id == User.id)
        .group_by(User.name)
        .all()
    )

    return {
        "live_visitors": live_visitors,
        "qualified_leads": qualified_leads,
        "total_leads": db.query(Lead).count(),
        "conversion_funnel": [{"stage": name, "count": count} for name, count in funnel],
        "agent_performance": [{"owner": name, "leads": count} for name, count in by_owner],
        # Revenue pipeline needs a per-lead deal value, which this schema
        # doesn't capture yet (average ticket size varies too much by
        # project to assume a number). Add a `deal_value` column on Lead
        # once the business defines it, and this becomes a real sum().
        "revenue_pipeline_note": "Add Lead.deal_value once average ticket size per project is defined.",
    }


@router.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: str, payload: LeadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "sales")),
):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(lead, field, value)
    db.add(AuditLog(actor_id=user.id, action="lead.update", target_type="lead", target_id=lead.id, meta=changes))
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/notes", response_model=NoteOut)
def add_note(
    lead_id: str, payload: NoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "sales")),
):
    if not db.get(Lead, lead_id):
        raise HTTPException(404, "Lead not found")
    note = Note(lead_id=lead_id, author_id=user.id, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/leads/{lead_id}/notes", response_model=list[NoteOut])
def list_notes(lead_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Note).filter(Note.lead_id == lead_id).order_by(Note.created_at.desc()).all()


@router.post("/leads/{lead_id}/tags")
def assign_tags(
    lead_id: str, payload: TagAssign,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "sales")),
):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    for name in payload.tag_names:
        tag = db.query(Tag).filter(Tag.name == name).one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        if tag not in lead.tags:
            lead.tags.append(tag)
    db.commit()
    return {"status": "ok", "tags": [t.name for t in lead.tags]}
