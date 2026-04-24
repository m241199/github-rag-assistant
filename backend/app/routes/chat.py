import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.query import QueryLog
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.retrieval import retrieve_relevant_chunks
from app.services.prompt_builder import build_prompt
from app.services.llm_service import generate_answer

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    try:
        chunks = retrieve_relevant_chunks(db=db, repo_id=payload.repo_id, question=payload.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not chunks:
        return ChatResponse(
            answer="I could not find indexed repository context for that question. Index the repository first, then try again.",
            sources=[],
        )

    prompt = build_prompt(payload.question, chunks)
    try:
        answer = generate_answer(prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sources = [
        ChatSource(
            file_path=chunk["metadata"].get("file_path", "unknown"),
            section_title=chunk["metadata"].get("section_title"),
            symbol_name=chunk["metadata"].get("symbol_name"),
            snippet=chunk["text"][:250],
        )
        for chunk in chunks
    ]

    db.add(QueryLog(
        id=str(uuid.uuid4()),
        repo_id=payload.repo_id,
        question=payload.question,
        answer=answer,
    ))
    db.commit()

    return ChatResponse(answer=answer, sources=sources)
