import os
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import app.db.models as db_models
from alembic import command

BASE_DIR = Path(__file__).resolve().parents[2]


def run_migrations(database_url: str) -> None:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.mark.integration
def test_migrations_and_basic_crud(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for migration smoke tests")

    monkeypatch.setenv("DATABASE_URL", database_url)
    run_migrations(database_url)

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        project = db_models.Project(slug="demo", name="Demo", settings={"tier": "dev"})
        thread = db_models.Thread(
            project=project, title="Hello", tags={"topic": "intro"}
        )
        message = db_models.Message(
            thread=thread,
            channel="web",
            role="user",
            content="Hello world",
            meta={"lang": "en"},
        )
        action = db_models.Action(
            thread=thread,
            type="example",
            policy_mode="DRAFT",
            status="DRAFT",
            payload={"input": "value"},
            idempotency_key="idem-1",
        )
        session.add_all([project, thread, message, action])
        session.commit()

        stored_project = session.execute(
            select(db_models.Project).where(db_models.Project.slug == "demo")
        ).scalar_one()
        stored_thread = session.execute(
            select(db_models.Thread).where(
                db_models.Thread.project_id == stored_project.id
            )
        ).scalar_one()
        stored_message = session.execute(
            select(db_models.Message).where(
                db_models.Message.thread_id == stored_thread.id
            )
        ).scalar_one()
        stored_action = session.execute(
            select(db_models.Action).where(db_models.Action.idempotency_key == "idem-1")
        ).scalar_one()

        assert stored_project.name == "Demo"
        assert stored_thread.title == "Hello"
        assert stored_message.content == "Hello world"
        assert stored_action.status == "DRAFT"
