from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_extensions():
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def ensure_schema_updates():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding_text TEXT"))
        ensure_vector_dimensions(connection)


def ensure_vector_dimensions(connection):
    result = connection.execute(text("""
        SELECT a.atttypmod
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = 'chunks'
          AND n.nspname = current_schema()
          AND a.attname = 'embedding'
          AND NOT a.attisdropped
    """)).scalar()

    expected_typmod = settings.embedding_dimensions
    if result is None:
        connection.execute(text(f"ALTER TABLE chunks ADD COLUMN embedding vector({settings.embedding_dimensions})"))
    elif result != expected_typmod:
        connection.execute(text("ALTER TABLE chunks DROP COLUMN embedding"))
        connection.execute(text(f"ALTER TABLE chunks ADD COLUMN embedding vector({settings.embedding_dimensions})"))
