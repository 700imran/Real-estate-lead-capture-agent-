"""Intent scoring — turns raw tracked events into a cold/warm/hot classification."""

EVENT_WEIGHTS = {
    "page_view": 5,
    "click": 3,
    "hover_interest": 4,
    "form_field_focus": 6,
    "form_submit": 30,
    "identify": 40,
    "scroll_depth": 2,
}
HIGH_INTENT_PATHS = ["/pricing", "/checkout", "/demo", "/contact", "/floor-plans"]
HOT_THRESHOLD = 80
WARM_THRESHOLD = 30


def score_events(events: list[dict], current_page: str | None) -> int:
    score = sum(EVENT_WEIGHTS.get(e.get("type"), 1) for e in events)
    if current_page and any(p in current_page for p in HIGH_INTENT_PATHS):
        score += 20
    return score


def classify(score: int) -> str:
    if score >= HOT_THRESHOLD:
        return "hot"
    if score >= WARM_THRESHOLD:
        return "warm"
    return "cold"


def repeat_visitor_bonus(session_count: int) -> int:
    """A visitor coming back for a 2nd/3rd session is a strong signal on its own."""
    return min((session_count - 1) * 15, 45) if session_count > 1 else 0
