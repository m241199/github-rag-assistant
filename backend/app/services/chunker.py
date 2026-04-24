import re
from typing import Any


MAX_CHUNK_TOKENS = 700
MIN_CHUNK_CHARS = 40
MIN_CHUNK_TOKENS = 8
LINE_WINDOW_SIZE = 80
LINE_WINDOW_OVERLAP = 10

SYMBOL_PATTERNS_BY_LANGUAGE: dict[str, list[tuple[str, str]]] = {
    "py": [
        (r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
        (r"^\s*async\s+def\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
        (r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
    ],
    "js": [
        (r"^\s*class\s+([A-Za-z_$][A-Za-z0-9_$]*)", "class"),
        (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)", "function"),
        (r"^\s*(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?\(", "function"),
        (r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?[A-Za-z_$]*\s*=>", "function"),
        (r"^\s*(?:static\s+|async\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*\{", "method"),
    ],
    "ts": [
        (r"^\s*(?:export\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)", "class"),
        (r"^\s*(?:export\s+)?(?:interface|type|enum)\s+([A-Za-z_$][A-Za-z0-9_$]*)", "type"),
        (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)", "function"),
        (r"^\s*(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*[:=]", "function"),
        (r"^\s*(?:public|private|protected|static|async|readonly|\s)+([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*[:A-Za-z0-9_<>,\s\[\]|?]*\{", "method"),
        (r"^\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*[:A-Za-z0-9_<>,\s\[\]|?]*\{", "method"),
    ],
    "tsx": [],
    "jsx": [],
    "java": [
        (r"^\s*(?:public|private|protected|abstract|final|static|\s)*(?:class|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
        (r"^\s*(?:public|private|protected|static|final|synchronized|abstract|native|\s)+[A-Za-z0-9_<>,\[\]?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)", "method"),
    ],
    "go": [
        (r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:struct|interface)", "type"),
        (r"^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)", "function"),
    ],
    "rs": [
        (r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)", "type"),
        (r"^\s*(?:pub\s+)?impl(?:\s+[A-Za-z_][A-Za-z0-9_]*)?", "impl"),
        (r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
    ],
    "cs": [
        (r"^\s*(?:public|private|protected|internal|static|abstract|sealed|partial|\s)*(?:class|interface|struct|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
        (r"^\s*(?:public|private|protected|internal|static|async|virtual|override|\s)+[A-Za-z0-9_<>,\[\]?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)", "method"),
    ],
    "php": [
        (r"^\s*(?:abstract\s+|final\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", "class"),
        (r"^\s*(?:public|private|protected|static|\s)*function\s+([A-Za-z_][A-Za-z0-9_]*)", "function"),
    ],
    "rb": [
        (r"^\s*class\s+([A-Za-z_][A-Za-z0-9_:]*)", "class"),
        (r"^\s*module\s+([A-Za-z_][A-Za-z0-9_:]*)", "module"),
        (r"^\s*def\s+(?:self\.)?([A-Za-z_][A-Za-z0-9_!?=]*)", "function"),
    ],
}

SYMBOL_PATTERNS_BY_LANGUAGE["tsx"] = SYMBOL_PATTERNS_BY_LANGUAGE["ts"]
SYMBOL_PATTERNS_BY_LANGUAGE["jsx"] = SYMBOL_PATTERNS_BY_LANGUAGE["js"]


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_document(text: str, file_type: str, path: str, language: str | None = None) -> list[dict[str, Any]]:
    if file_type == "markdown":
        return with_embedding_text(chunk_markdown(text, path))
    if file_type == "code":
        return with_embedding_text(chunk_code(text, path, language))
    return with_embedding_text(chunk_plain_text(text, path))


def chunk_markdown(text: str, path: str) -> list[dict[str, Any]]:
    pattern = r"(?m)^#{1,6}\s+.*$"
    matches = list(re.finditer(pattern, text))

    if not matches:
        return chunk_plain_text(text, path)

    chunks = []

    preamble = text[:matches[0].start()].strip()
    if preamble:
        chunks.append({
            "text": preamble,
            "metadata": {
                "file_path": path,
                "chunk_type": "markdown_preamble",
                "section_title": None,
                "start_line": 1,
                "end_line": preamble.count("\n") + 1,
            }
        })

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        first_line = section.splitlines()[0] if section.splitlines() else "Untitled"
        title = first_line.lstrip("#").strip()
        metadata = {
            "file_path": path,
            "section_title": title,
            "start_line": text[:start].count("\n") + 1,
            "end_line": text[:end].count("\n") + 1,
        }

        if estimate_tokens(section) <= MAX_CHUNK_TOKENS:
            chunks.append({"text": section, "metadata": {**metadata, "chunk_type": "markdown_section"}})
        else:
            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            for idx, paragraph in enumerate(paragraphs):
                chunks.append({
                    "text": paragraph,
                    "metadata": {
                        **metadata,
                        "chunk_type": "markdown_subsection",
                        "subchunk_index": idx,
                    }
                })

    return chunks


def chunk_code(text: str, path: str, language: str | None = None) -> list[dict[str, Any]]:
    lines = text.splitlines()
    boundaries = find_symbol_boundaries(lines, language)

    if not boundaries:
        return chunk_by_line_window(text, path, language=language, chunk_size=40, overlap=5)

    chunks = []
    module_prefix_end = boundaries[0]["start_idx"]
    module_prefix = "\n".join(lines[:module_prefix_end]).strip()
    if module_prefix:
        chunks.append({
            "text": module_prefix,
            "metadata": {
                "file_path": path,
                "chunk_type": "code_module_preamble",
                "symbol_name": None,
                "symbol_type": "module",
                "language": language,
                "start_line": 1,
                "end_line": module_prefix_end,
            }
        })

    for i, boundary in enumerate(boundaries):
        start_idx = boundary["start_idx"]
        end_idx = boundaries[i + 1]["start_idx"] if i + 1 < len(boundaries) else len(lines)
        snippet = "\n".join(lines[start_idx:end_idx]).strip()

        if not snippet:
            continue

        metadata = {
            "file_path": path,
            "chunk_type": "code_symbol",
            "symbol_name": boundary["symbol_name"],
            "symbol_type": boundary["symbol_type"],
            "parent_symbol_name": boundary.get("parent_symbol_name"),
            "parent_symbol_type": boundary.get("parent_symbol_type"),
            "language": language,
            "start_line": start_idx + 1,
            "end_line": end_idx,
        }
        chunks.extend(split_large_code_symbol(snippet, metadata, language))

    return chunks


def find_symbol_boundaries(lines: list[str], language: str | None = None) -> list[dict[str, Any]]:
    patterns = get_symbol_patterns(language)
    boundaries: list[dict[str, Any]] = []
    seen: set[int] = set()

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "*")):
            continue

        for pattern, symbol_type in patterns:
            match = re.match(pattern, line)
            if not match or idx in seen:
                continue

            symbol_name = match.group(1) if match.groups() and match.group(1) else symbol_type
            if symbol_name in {"if", "for", "while", "switch", "catch"}:
                continue

            boundaries.append({
                "start_idx": idx,
                "symbol_name": symbol_name,
                "symbol_type": symbol_type,
                "indent": len(line) - len(line.lstrip()),
            })
            seen.add(idx)
            break

    return add_parent_symbol_metadata(boundaries)


def add_parent_symbol_metadata(boundaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_stack: list[dict[str, Any]] = []
    parent_symbol_types = {"class", "type", "impl", "module"}

    for boundary in boundaries:
        indent = boundary["indent"]
        while parent_stack and parent_stack[-1]["indent"] >= indent:
            parent_stack.pop()

        if parent_stack:
            parent = parent_stack[-1]
            boundary["parent_symbol_name"] = parent["symbol_name"]
            boundary["parent_symbol_type"] = parent["symbol_type"]

        if boundary["symbol_type"] in parent_symbol_types:
            parent_stack.append(boundary)

    return boundaries


def get_symbol_patterns(language: str | None) -> list[tuple[str, str]]:
    if not language:
        return [
            pattern
            for patterns in SYMBOL_PATTERNS_BY_LANGUAGE.values()
            for pattern in patterns
        ]

    normalized = language.lower()
    return SYMBOL_PATTERNS_BY_LANGUAGE.get(normalized, [])


def split_large_code_symbol(
    snippet: str,
    metadata: dict[str, Any],
    language: str | None,
) -> list[dict[str, Any]]:
    if estimate_tokens(snippet) <= MAX_CHUNK_TOKENS:
        return [{"text": snippet, "metadata": metadata}]

    lines = snippet.splitlines()
    nested_boundaries = find_symbol_boundaries(lines[1:], language)

    if nested_boundaries:
        chunks = []
        prefix = lines[0].strip()
        shifted_boundaries = [
            {**boundary, "start_idx": boundary["start_idx"] + 1}
            for boundary in nested_boundaries
        ]

        for idx, boundary in enumerate(shifted_boundaries):
            start_idx = boundary["start_idx"]
            end_idx = shifted_boundaries[idx + 1]["start_idx"] if idx + 1 < len(shifted_boundaries) else len(lines)
            text = "\n".join(([prefix] if prefix else []) + lines[start_idx:end_idx]).strip()
            if not text:
                continue

            chunks.extend(split_large_code_symbol(text, {
                **metadata,
                "chunk_type": "code_symbol_child",
                "parent_symbol_name": metadata.get("symbol_name"),
                "parent_symbol_type": metadata.get("symbol_type"),
                "symbol_name": boundary["symbol_name"],
                "symbol_type": boundary["symbol_type"],
                "start_line": metadata["start_line"] + start_idx,
                "end_line": metadata["start_line"] + end_idx - 1,
            }, language))

        if chunks:
            return chunks

    return split_code_by_line_window(snippet, metadata)


def split_code_by_line_window(snippet: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    lines = snippet.splitlines()
    chunks = []
    start = 0
    window_index = 0

    while start < len(lines):
        end = min(start + LINE_WINDOW_SIZE, len(lines))
        text = "\n".join(lines[start:end]).strip()
        if text:
            chunks.append({
                "text": text,
                "metadata": {
                    **metadata,
                    "chunk_type": "code_symbol_window",
                    "parent_symbol_name": metadata.get("symbol_name"),
                    "parent_symbol_type": metadata.get("symbol_type"),
                    "window_index": window_index,
                    "start_line": metadata["start_line"] + start,
                    "end_line": metadata["start_line"] + end - 1,
                }
            })
            window_index += 1

        if end == len(lines):
            break
        start = max(0, end - LINE_WINDOW_OVERLAP)

    return chunks


def chunk_plain_text(text: str, path: str) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = estimate_tokens(paragraph)
        if current and current_len + paragraph_len > 500:
            chunks.append({
                "text": "\n\n".join(current),
                "metadata": {
                    "file_path": path,
                    "chunk_type": "text_block",
                }
            })
            current = [paragraph]
            current_len = paragraph_len
        else:
            current.append(paragraph)
            current_len += paragraph_len

    if current:
        chunks.append({
            "text": "\n\n".join(current),
            "metadata": {
                "file_path": path,
                "chunk_type": "text_block",
            }
        })

    return chunks


def chunk_by_line_window(
    text: str,
    path: str,
    language: str | None = None,
    chunk_size: int = 40,
    overlap: int = 5,
) -> list[dict[str, Any]]:
    lines = text.splitlines()
    chunks = []
    start = 0

    while start < len(lines):
        end = min(start + chunk_size, len(lines))
        snippet = "\n".join(lines[start:end]).strip()

        if snippet:
            chunks.append({
                "text": snippet,
                "metadata": {
                    "file_path": path,
                    "chunk_type": "code_fallback",
                    "language": language,
                    "start_line": start + 1,
                    "end_line": end,
                }
            })

        if end == len(lines):
            break

        start = end - overlap

    return chunks


def with_embedding_text(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered_chunks = [chunk for chunk in chunks if should_keep_chunk(chunk)]
    for chunk in filtered_chunks:
        chunk["embedding_text"] = build_embedding_text(chunk["text"], chunk["metadata"])
    return filtered_chunks


def should_keep_chunk(chunk: dict[str, Any]) -> bool:
    text = chunk["text"].strip()
    metadata = chunk["metadata"]

    if not text:
        return False

    if is_low_signal_code_symbol(text, metadata):
        return False

    if metadata.get("section_title") or metadata.get("symbol_name"):
        return estimate_tokens(text) >= 3

    return len(text) >= MIN_CHUNK_CHARS and estimate_tokens(text) >= MIN_CHUNK_TOKENS


def is_low_signal_code_symbol(text: str, metadata: dict[str, Any]) -> bool:
    if not metadata.get("symbol_name"):
        return False

    body_lines = [
        line.strip()
        for line in text.splitlines()[1:]
        if line.strip() and not line.strip().startswith(("#", "//"))
    ]
    if not body_lines:
        return True

    normalized_body = " ".join(body_lines)
    return normalized_body in {"pass", "...", "return None", "return", "{}"}


def build_embedding_text(text: str, metadata: dict[str, Any]) -> str:
    lines = [f"File: {metadata.get('file_path', 'unknown')}"]

    language = metadata.get("language")
    if language:
        lines.append(f"Language: {language}")

    section_title = metadata.get("section_title")
    if section_title:
        lines.append(f"Section: {section_title}")

    parent_symbol_name = metadata.get("parent_symbol_name")
    if parent_symbol_name:
        lines.append(f"Parent symbol: {parent_symbol_name}")

    symbol_name = metadata.get("symbol_name")
    if symbol_name:
        lines.append(f"Symbol: {symbol_name}")

    symbol_type = metadata.get("symbol_type")
    if symbol_type:
        lines.append(f"Symbol type: {symbol_type}")

    return "\n".join(lines + ["", text])
