import json
from functools import lru_cache
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.config import settings


def embed_text(text: str) -> list[float]:
    if settings.embedding_provider == "local":
        return embed_text_local(text)

    if settings.embedding_provider == "openai":
        return embed_text_openai(text)

    raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider}")


@lru_cache(maxsize=1)
def get_local_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Local embeddings require sentence-transformers. "
            "Run `pip install -r requirements.txt` from the backend folder."
        ) from exc

    return SentenceTransformer(settings.embedding_model)


def embed_text_local(text: str) -> list[float]:
    model = get_local_embedding_model()
    embedding = model.encode(text[:24_000], normalize_embeddings=True)
    return embedding.tolist()


def embed_text_openai(text: str) -> list[float]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to create embeddings.")

    payload = json.dumps({
        "model": settings.embedding_model,
        "input": text[:24_000],
        "dimensions": settings.embedding_dimensions,
    }).encode("utf-8")

    request = Request(
        "https://api.openai.com/v1/embeddings",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI embeddings request failed with HTTP {exc.code}: {detail}") from exc

    return data["data"][0]["embedding"]
