import argparse
import json
from typing import Any

from app.services.chunker import chunk_document
from app.services.file_parser import parse_file
from app.services.github_loader import load_repository


def prepare_repository_index(repo_url: str) -> dict[str, Any]:
    repo = load_repository(repo_url)
    indexed_files = []
    total_chunks = 0

    for source_file in repo["files"]:
        parsed = parse_file(source_file["path"], source_file["content"])
        chunks = chunk_document(
            text=parsed.text,
            file_type=parsed.file_type,
            path=source_file["path"],
            language=parsed.language,
        )

        indexed_files.append({
            "path": source_file["path"],
            "content": parsed.text,
            "file_type": parsed.file_type,
            "language": parsed.language,
            "size_chars": len(parsed.text),
            "chunk_count": len(chunks),
            "chunks": chunks,
        })
        total_chunks += len(chunks)

    return {
        "repo": {
            "url": repo["url"],
            "name": repo["name"],
            "branch": repo["branch"],
        },
        "filter_stats": repo.get("filter_stats", {}),
        "file_count": len(indexed_files),
        "total_chunks": total_chunks,
        "files": indexed_files,
    }


def index_repository_preview(
    repo_url: str,
    file_limit: int = 20,
    sample_chunks: int = 2,
) -> dict[str, Any]:
    prepared = prepare_repository_index(repo_url)

    return {
        "repo": prepared["repo"],
        "filter_stats": prepared["filter_stats"],
        "file_count": prepared["file_count"],
        "total_chunks": prepared["total_chunks"],
        "files": [
            {
                "path": file["path"],
                "file_type": file["file_type"],
                "language": file["language"],
                "size_chars": file["size_chars"],
                "chunk_count": file["chunk_count"],
                "sample_chunks": [
                    summarize_chunk(chunk)
                    for chunk in file["chunks"][:sample_chunks]
                ],
            }
            for file in prepared["files"][:file_limit]
        ],
    }


def summarize_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "text_preview": chunk["text"][:300],
        "embedding_text_preview": chunk["embedding_text"][:400],
        "metadata": chunk["metadata"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview repository indexing without using the database.")
    parser.add_argument("repo_url", help="GitHub repository URL, for example https://github.com/owner/repo")
    parser.add_argument("--file-limit", type=int, default=20, help="Number of indexed files to print")
    parser.add_argument("--sample-chunks", type=int, default=2, help="Number of sample chunks per printed file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    preview = index_repository_preview(
        repo_url=args.repo_url,
        file_limit=args.file_limit,
        sample_chunks=args.sample_chunks,
    )
    print(json.dumps(preview, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
