"""
AI Sales Agent — natural conversation, FAQ answering, lead qualification,
and appointment booking, backed by the GPT-4o -> Claude fallback chain.

Tool-calling here is deliberately simple: the system prompt asks the model
to emit inline markers (`[BOOK_APPOINTMENT: ...]`, `[QUALIFY: hot|warm|cold]`)
which get parsed out of the reply and turned into real DB side effects. This
is a foundation, not the final word — swap `_extract_actions` for native
OpenAI/Anthropic structured tool-calling once the conversation flows are
locked down and you want stricter guarantees than regex parsing gives you.
"""
import re

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Conversation, Message, Lead, Appointment, Prompt
from ..schemas import AgentChatRequest, AgentChatResponse
from ..services.ai_fallback import generate_with_fallback
from ..worker import summarize_conversation

router = APIRouter()

DEFAULT_SYSTEM_PROMPT = (
    "You are the sales assistant for a real estate developer's website. "
    "Answer questions about the project naturally, help the visitor compare "
    "unit types, and when they show genuine buying interest, offer to book a "
    "site visit. Keep replies short — 2-4 sentences. "
    "When the visitor agrees to a site visit or call, end your reply with "
    "a line in the exact format [BOOK_APPOINTMENT: <what they asked for, in "
    "plain text>]. If the conversation makes it clear this is a serious, "
    "qualified buyer, end with [QUALIFY: hot]; if they're comparing options "
    "casually, use [QUALIFY: warm]. Omit these markers otherwise."
)

APPOINTMENT_RE = re.compile(r"\[BOOK_APPOINTMENT:\s*(.*?)\]", re.IGNORECASE)
QUALIFY_RE = re.compile(r"\[QUALIFY:\s*(hot|warm|cold)\]", re.IGNORECASE)


def _system_prompt(db: Session, language: str) -> str:
    row = db.query(Prompt).filter(Prompt.name == "sales_agent_system_prompt").one_or_none()
    base = row.content if row else DEFAULT_SYSTEM_PROMPT
    if language == "hi":
        base += " Respond in conversational Hindi (Devanagari script) unless the visitor writes in English."
    return base


def _extract_actions(db: Session, reply: str, lead: Lead | None) -> str:
    """Parses action markers out of the model's reply, executes the
    corresponding DB write, and returns the reply with markers stripped
    (visitors should never see the raw marker text)."""
    appt_match = APPOINTMENT_RE.search(reply)
    if appt_match and lead:
        db.add(Appointment(lead_id=lead.id, status="requested", notes=appt_match.group(1).strip()))

    qualify_match = QUALIFY_RE.search(reply)
    if qualify_match and lead:
        lead.temperature = qualify_match.group(1).lower()

    clean = APPOINTMENT_RE.sub("", reply)
    clean = QUALIFY_RE.sub("", clean).strip()
    return clean


@router.post("/agent/chat", response_model=AgentChatResponse)
async def chat(payload: AgentChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.visitor_id == payload.visitor_id).one_or_none()

    conversation = None
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
    if not conversation:
        conversation = Conversation(
            visitor_id=payload.visitor_id,
            lead_id=lead.id if lead else None,
            language=payload.language,
        )
        db.add(conversation)
        db.flush()

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )
    llm_messages = [{"role": m.role, "content": m.content} for m in history if m.role in ("user", "assistant")]

    system_prompt = _system_prompt(db, payload.language)
    if payload.property_name:
        context_line = (
            f" The visitor is currently looking at {payload.property_name}; answer with that development in mind unless they ask about something else."
            if payload.language != "hi"
            else f" विज़िटर अभी {payload.property_name} देख रहा है; जब तक वह कुछ और न पूछे, इसी प्रोजेक्ट को ध्यान में रखकर जवाब दें।"
        )
        system_prompt += context_line

    reply = await generate_with_fallback(llm_messages, system=system_prompt)
    reply = reply or (
        "Sorry, I'm having trouble responding right now — please leave your number and our team will call you back."
        if payload.language != "hi"
        else "Maaf kijiye, abhi jawab dene mein dikkat ho rahi hai — apna number chhodiye, team call karegi."
    )

    clean_reply = _extract_actions(db, reply, lead)
    db.add(Message(conversation_id=conversation.id, role="assistant", content=clean_reply))
    db.commit()

    # Summarize long-running conversations in the background so the
    # dashboard can show a one-line gist without re-reading every message.
    if len(history) > 0 and len(history) % 6 == 0:
        background_tasks.add_task(summarize_conversation, conversation.id)

    return AgentChatResponse(conversation_id=conversation.id, reply=clean_reply)
