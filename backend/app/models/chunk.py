from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON

from app.config import settings
from app.db import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, index=True)
    repo_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default={})
    embedding = Column(Vector(settings.embedding_dimensions), nullable=True)
