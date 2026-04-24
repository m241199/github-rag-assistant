from typing import Any


def build_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    context_blocks = []

    for idx, chunk in enumerate(chunks, start=1):
        file_path = chunk["metadata"].get("file_path", "unknown")
        section_title = chunk["metadata"].get("section_title")
        symbol_name = chunk["metadata"].get("symbol_name")

        header = f"[Source {idx}] File: {file_path}"
        if section_title:
            header += f" | Section: {section_title}"
        if symbol_name:
            header += f" | Symbol: {symbol_name}"

        context_blocks.append(f"{header}\n{chunk['text']}")

    context = "\n\n".join(context_blocks)

    return f"""
You are a GitHub repository assistant.

Answer the user's question using only the provided context.
If the answer is not supported by the context, say so clearly.
Cite source numbers like [Source 1] when relevant.

Question:
{question}

Context:
{context}
""".strip()