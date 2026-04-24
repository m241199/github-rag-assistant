from sqlalchemy import Column, String, Text, ForeignKey

from app.db import Base


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    repo_id = Column(String, ForeignKey("repositories.id"), nullable=False, index=True)
    path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    language = Column(String, nullable=True)
    content = Column(Text, nullable=False)