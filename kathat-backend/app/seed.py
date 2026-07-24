"""Run once after the database is up: `python -m app.seed`
Creates the default pipeline stages, a starter prompt, and one admin user
so there's a way to log in for the first time."""
import os

from .database import Base, engine, SessionLocal
from .models import PipelineStage, User, Prompt
from .security import hash_password
from .routers.agent import DEFAULT_SYSTEM_PROMPT

DEFAULT_STAGES = ["New", "Contacted", "Site Visit", "Booked", "Lost"]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(PipelineStage).count():
            for i, name in enumerate(DEFAULT_STAGES):
                db.add(PipelineStage(name=name, position=i))

        if not db.query(Prompt).filter(Prompt.name == "sales_agent_system_prompt").one_or_none():
            db.add(Prompt(name="sales_agent_system_prompt", content=DEFAULT_SYSTEM_PROMPT))

        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
        if not db.query(User).filter(User.email == admin_email).one_or_none():
            admin_password = os.getenv("SEED_ADMIN_PASSWORD", "changeme123")
            db.add(User(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                name="Admin",
                role="admin",
            ))
            print(f"Seeded admin user: {admin_email} / {admin_password} — change this password immediately.")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
