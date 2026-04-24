from dataclasses import dataclass


@dataclass
class ParsedFile:
    text: str
    file_type: str
    language: str | None


def parse_file(path: str, content: str) -> ParsedFile:
    lower_path = path.lower()

    if lower_path.endswith((".md", ".mdx", ".rst")):
        return ParsedFile(text=content, file_type="markdown", language=None)

    if lower_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".cs", ".php", ".rb")):
        language = lower_path.rsplit(".", 1)[-1]
        return ParsedFile(text=content, file_type="code", language=language)

    return ParsedFile(text=content, file_type="text", language=None)
