import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.repo import Repository
from app.schemas.repo import RepoCreate, RepoResponse
from app.services.github_loader import parse_github_url

router = APIRouter()


@router.post("/", response_model=RepoResponse)
def create_repo(payload: RepoCreate, db: Session = Depends(get_db)):
    try:
        _, repo_name = parse_github_url(payload.github_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    existing = (
        db.query(Repository)
        .filter(Repository.github_url == payload.github_url)
        .one_or_none()
    )
    if existing:
        return existing

    repo = Repository(
        id=str(uuid.uuid4()),
        github_url=payload.github_url,
        name=repo_name,
        branch="main",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo
