from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, index=True)
    github_url = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    branch = Column(String, nullable=False, default="main")
    indexed_at = Column(DateTime(timezone=True), server_default=func.now())