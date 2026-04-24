from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, index=True)
    repo_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())