"""
Data model for the Agentic Revenue Engine.

Covers: auth/RBAC, visitor + event tracking, the lead/CRM lifecycle
(notes, tags, pipeline stages, owner assignment), AI agent conversations,
appointments, editable prompt config, and an audit trail.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, JSON, String, Table, Text, Column, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def uid() -> str:
    return str(uuid.uuid4())


# ---- Auth / RBAC -----------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    # admin: full access · sales: own leads + assigned · viewer: read-only
    role: Mapped[str] = mapped_column(String, default="sales")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owned_leads: Mapped[list["Lead"]] = relationship(back_populates="owner")


# ---- Visitor tracking --------------------------------------------------------
class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # visitor_id from the pixel
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    session_count: Mapped[int] = mapped_column(Integer, default=1)
    is_repeat: Mapped[bool] = mapped_column(Boolean, default=False)

    events: Mapped[list["Event"]] = relationship(back_populates="visitor")
    lead: Mapped["Lead | None"] = relationship(back_populates="visitor", uselist=False)


class VisitorSession(Base):
    """One row per (visitor, session) pair seen — powers repeat-visitor
    detection without Redis. A visitor's session_count is just how many
    distinct rows exist for that visitor_id."""
    __tablename__ = "visitor_sessions"
    __table_args__ = (UniqueConstraint("visitor_id", "session_id", name="uq_visitor_session"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    visitor_id: Mapped[str] = mapped_column(ForeignKey("visitors.id"), index=True)
    session_id: Mapped[str] = mapped_column(String)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    """One row per tracked interaction — the raw material for intent scoring
    and the session timeline shown in the dashboard."""
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    visitor_id: Mapped[str] = mapped_column(ForeignKey("visitors.id"), index=True)
    type: Mapped[str] = mapped_column(String)  # page_view, click, hover_interest, form_field_focus, form_submit, identify, scroll_depth
    page: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    visitor: Mapped["Visitor"] = relationship(back_populates="events")


# ---- CRM: pipeline, leads, notes, tags --------------------------------------
class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String, unique=True)  # New, Contacted, Site Visit, Booked, Lost
    position: Mapped[int] = mapped_column(Integer, default=0)

    leads: Mapped[list["Lead"]] = relationship(back_populates="pipeline_stage")


lead_tags = Table(
    "lead_tags", Base.metadata,
    Column("lead_id", ForeignKey("leads.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String, unique=True)

    leads: Mapped[list["Lead"]] = relationship(secondary=lead_tags, back_populates="tags")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    visitor_id: Mapped[str | None] = mapped_column(ForeignKey("visitors.id"), unique=True, nullable=True)

    name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    language: Mapped[str] = mapped_column(String, default="en")  # "en" | "hi"

    source_page: Mapped[str | None] = mapped_column(String, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    temperature: Mapped[str] = mapped_column(String, default="cold")  # cold | warm | hot

    pipeline_stage_id: Mapped[str | None] = mapped_column(ForeignKey("pipeline_stages.id"), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    visitor: Mapped["Visitor | None"] = relationship(back_populates="lead")
    pipeline_stage: Mapped["PipelineStage | None"] = relationship(back_populates="leads")
    owner: Mapped["User | None"] = relationship(back_populates="owned_leads")
    notes: Mapped[list["Note"]] = relationship(back_populates="lead", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship(secondary=lead_tags, back_populates="leads")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    author_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="notes")


# ---- AI Sales Agent: conversations + appointments ---------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    visitor_id: Mapped[str | None] = mapped_column(ForeignKey("visitors.id"), nullable=True)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
    language: Mapped[str] = mapped_column(String, default="en")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # filled in by the summarization worker job
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), index=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="requested")  # requested | confirmed | completed | cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="appointments")


# ---- Admin: AI config / prompt management / audit ---------------------------
class Prompt(Base):
    """Editable system prompts for the AI sales agent — the foundation of
    the admin 'prompt management' feature. Versioned by simple overwrite;
    promote to a history table if full version control is needed later."""
    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String, unique=True)  # e.g. "sales_agent_system_prompt"
    content: Mapped[str] = mapped_column(Text)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String)  # e.g. "lead.reassign", "prompt.update"
    target_type: Mapped[str | None] = mapped_column(String, nullable=True)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
