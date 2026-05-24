from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models.agent  # noqa: F401
    import app.models.chunk  # noqa: F401
    import app.models.conversation  # noqa: F401
    import app.models.knowledge_base  # noqa: F401
    import app.models.knowledge_item  # noqa: F401
    import app.models.message  # noqa: F401

    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """SQLite 无 Alembic 时补列。"""
    from sqlalchemy import inspect, text

    if not settings.database_url.startswith("sqlite"):
        return
    insp = inspect(engine)
    if "conversations" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("conversations")}
        if "agent_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE conversations ADD COLUMN agent_id VARCHAR(36)"))
