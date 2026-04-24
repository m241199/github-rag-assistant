import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass
class Settings:
    app_name: str = "GitHub RAG Assistant"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/github_rag"
    )
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    chat_model: str = os.getenv("CHAT_MODEL", "gemini-2.5-flash-lite")


settings = Settings()
