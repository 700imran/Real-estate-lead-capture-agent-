from datetime import datetime
from pydantic import BaseModel, Field


# ---- Tracking ingestion (matches the pixel's beacon payload) ----------------
class TrackEvent(BaseModel):
    type: str
    data: dict = Field(default_factory=dict)
    t: int | None = None
    page: str | None = None


class TrackPayload(BaseModel):
    visitor_id: str
    session_id: str | None = None
    email: str | None = None
    phone: str | None = None
    current_page: str | None = None
    referrer: str | None = None
    events: list[TrackEvent] = Field(default_factory=list)


class TrackResponse(BaseModel):
    status: str
    score: int
    temperature: str


# ---- Auth --------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


# ---- Leads / CRM --------------------------------------------------------------
class LeadOut(BaseModel):
    id: str
    name: str | None
    email: str | None
    phone: str | None
    language: str
    source_page: str | None
    score: int
    temperature: str
    pipeline_stage_id: str | None
    owner_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    name: str | None = None
    owner_id: str | None = None
    pipeline_stage_id: str | None = None
    temperature: str | None = None


class NoteCreate(BaseModel):
    body: str


class NoteOut(BaseModel):
    id: str
    body: str
    author_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TagAssign(BaseModel):
    tag_names: list[str]


# ---- AI Sales Agent ------------------------------------------------------------
class AgentChatRequest(BaseModel):
    visitor_id: str
    conversation_id: str | None = None
    message: str
    language: str = "en"
    property_slug: str | None = None
    property_name: str | None = None


class AgentChatResponse(BaseModel):
    conversation_id: str
    reply: str


class AppointmentCreate(BaseModel):
    lead_id: str
    scheduled_for: datetime | None = None
    notes: str | None = None


class AppointmentOut(BaseModel):
    id: str
    lead_id: str
    scheduled_for: datetime | None
    status: str

    class Config:
        from_attributes = True


# ---- Admin: prompt management --------------------------------------------------
class PromptUpsert(BaseModel):
    name: str
    content: str


class PromptOut(BaseModel):
    name: str
    content: str
    updated_at: datetime

    class Config:
        from_attributes = True
