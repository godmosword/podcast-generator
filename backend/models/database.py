from __future__ import annotations

from pathlib import Path

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DB_PATH = Path("output/wavescript.db")
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="queued")
    progress = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=False, default="")
    output_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_provider = Column(String, nullable=True)
    request_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


Base.metadata.create_all(bind=engine)

# Migrate existing databases that predate new columns.
_NEW_COLUMNS = [
    ("retry_count", "ALTER TABLE jobs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0"),
    ("last_provider", "ALTER TABLE jobs ADD COLUMN last_provider VARCHAR"),
    ("request_payload", "ALTER TABLE jobs ADD COLUMN request_payload TEXT"),
]
with engine.connect() as _conn:
    _existing = {col["name"] for col in inspect(engine).get_columns("jobs")}
    for _col, _ddl in _NEW_COLUMNS:
        if _col not in _existing:
            _conn.execute(text(_ddl))
    _conn.commit()
