from typing import Any

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.embeddings import embed_text


def retrieve_relevant_chunks(
    db: Session,
    repo_id: str,
    question: str,
    limit: int = 6,
) -> list[dict[str, Any]]:
    query_embedding = embed_text(question)
    distance = Chunk.embedding.cosine_distance(query_embedding)

    rows = (
        db.query(Chunk, distance.label("distance"))
        .filter(Chunk.repo_id == repo_id)
        .filter(Chunk.embedding.isnot(None))
        .order_by(distance)
        .limit(limit)
        .all()
    )

    return [
        {
            "text": chunk.text,
            "metadata": chunk.metadata_json,
            "score": 1 - float(distance_value or 0),
            "distance": float(distance_value or 0),
        }
        for chunk, distance_value in rows
    ]
