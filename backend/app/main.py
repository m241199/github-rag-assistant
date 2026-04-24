from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.repos import router as repos_router
from app.routes.indexing import router as indexing_router
from app.routes.chat import router as chat_router
from app.db import Base, engine, ensure_database_extensions, ensure_schema_updates
from app.models import chunk, file, query, repo

app = FastAPI(title="GitHub RAG Assistant", version="0.1.0")

ensure_database_extensions()
Base.metadata.create_all(bind=engine)
ensure_schema_updates()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos_router, prefix="/repos", tags=["repos"])
app.include_router(indexing_router, prefix="/indexing", tags=["indexing"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])


@app.get("/")
def root():
    return {"message": "GitHub RAG Assistant backend is running"}
