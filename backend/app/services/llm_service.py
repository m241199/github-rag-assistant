import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.config import settings


def generate_answer(prompt: str) -> str:
    if settings.llm_provider == "gemini":
        return generate_answer_gemini(prompt)

    if settings.llm_provider == "openai":
        return generate_answer_openai(prompt)

    raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def generate_answer_gemini(prompt: str) -> str:
    if not settings.gemini_api_key:
        return (
            "I found relevant repository context, but no GEMINI_API_KEY is configured, "
            "so I cannot generate a model answer yet. The cited sources below are the "
            "retrieved chunks that would be sent to the chat model."
        )

    payload = json.dumps({
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
    }).encode("utf-8")

    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.chat_model}:generateContent?key={settings.gemini_api_key}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini chat request failed with HTTP {exc.code}: {detail}") from exc

    return extract_gemini_text(data)


def generate_answer_openai(prompt: str) -> str:
    if not settings.openai_api_key:
        return (
            "I found relevant repository context, but no OPENAI_API_KEY is configured, "
            "so I cannot generate a model answer yet. The cited sources below are the "
            "retrieved chunks that would be sent to the chat model."
        )

    payload = json.dumps({
        "model": settings.chat_model,
        "input": prompt,
    }).encode("utf-8")

    request = Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI chat request failed with HTTP {exc.code}: {detail}") from exc

    return extract_response_text(data)


def extract_gemini_text(data: dict) -> str:
    parts: list[str] = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)

    return "\n".join(parts).strip() or "No answer text was returned by Gemini."


def extract_response_text(data: dict) -> str:
    if data.get("output_text"):
        return data["output_text"]

    parts: list[str] = []
    for output_item in data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if text:
                parts.append(text)

    return "\n".join(parts).strip() or "No answer text was returned by the model."
