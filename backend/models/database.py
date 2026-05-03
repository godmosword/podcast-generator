from __future__ import annotations

from pathlib import Path

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DB_PATH = Path("output/wavescript.db")
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False, default="未命名 Podcast")
    script = Column(Text, nullable=False, default="")
    hosts = Column(JSON, nullable=False, default=list)
    voice_map = Column(JSON, nullable=False, default=dict)
    bgm_id = Column(String, nullable=True)
    speaker_settings = Column(JSON, nullable=True)
    last_generated_job_id = Column(String, nullable=True)
    chapters = Column(JSON, nullable=True)
    show_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


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
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Segment(Base):
    __tablename__ = "segments"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=True)
    index = Column(Integer, nullable=False)
    speaker = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    start_ms = Column(Integer, nullable=False, default=0)
    end_ms = Column(Integer, nullable=False, default=0)
    audio_path = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


Base.metadata.create_all(bind=engine)

# Migrate existing databases that predate new columns.
_NEW_JOB_COLUMNS = [
    ("retry_count", "ALTER TABLE jobs ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0"),
    ("last_provider", "ALTER TABLE jobs ADD COLUMN last_provider VARCHAR"),
    ("request_payload", "ALTER TABLE jobs ADD COLUMN request_payload TEXT"),
    ("project_id", "ALTER TABLE jobs ADD COLUMN project_id VARCHAR REFERENCES projects(id)"),
]
with engine.connect() as _conn:
    _existing = {col["name"] for col in inspect(engine).get_columns("jobs")}
    for _col, _ddl in _NEW_JOB_COLUMNS:
        if _col not in _existing:
            _conn.execute(text(_ddl))
    _conn.commit()

_NEW_PROJECT_COLUMNS = [
    ("chapters", "ALTER TABLE projects ADD COLUMN chapters JSON"),
    ("show_notes", "ALTER TABLE projects ADD COLUMN show_notes TEXT"),
]
with engine.connect() as _conn:
    _existing_proj = {col["name"] for col in inspect(engine).get_columns("projects")}
    for _col, _ddl in _NEW_PROJECT_COLUMNS:
        if _col not in _existing_proj:
            _conn.execute(text(_ddl))
    _conn.commit()
