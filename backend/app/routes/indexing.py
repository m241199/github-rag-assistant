import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.chunk import Chunk
from app.models.file import FileRecord
from app.models.repo import Repository
from app.services.embeddings import embed_text
from app.services.indexing_service import prepare_repository_index

router = APIRouter()


@router.post("/{repo_id}")
def index_repo(repo_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        prepared_index = prepare_repository_index(repo.github_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load GitHub repository: {exc}") from exc

    db.query(Chunk).filter(Chunk.repo_id == repo_id).delete()
    db.query(FileRecord).filter(FileRecord.repo_id == repo_id).delete()

    file_count = 0
    chunk_count = 0

    for indexed_file in prepared_index["files"]:
        file_record = FileRecord(
            id=str(uuid.uuid4()),
            repo_id=repo_id,
            path=indexed_file["path"],
            file_type=indexed_file["file_type"],
            language=indexed_file["language"],
            content=indexed_file["content"],
        )
        db.add(file_record)
        db.flush()
        file_count += 1

        for index, chunk in enumerate(indexed_file["chunks"]):
            try:
                embedding = embed_text(chunk["embedding_text"])
            except RuntimeError as exc:
                db.rollback()
                raise HTTPException(status_code=502, detail=str(exc)) from exc

            db.add(Chunk(
                id=str(uuid.uuid4()),
                repo_id=repo_id,
                file_id=file_record.id,
                chunk_index=index,
                text=chunk["text"],
                embedding_text=chunk["embedding_text"],
                metadata_json=chunk["metadata"],
                embedding=embedding,
            ))
            chunk_count += 1

    repo.branch = prepared_index["repo"]["branch"]
    db.commit()

    return {
        "repo_id": repo_id,
        "status": "indexed",
        "branch": repo.branch,
        "files": file_count,
        "chunks": chunk_count,
    }
