from io import BytesIO
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import ZipFile

from app.config import settings


MAX_FILE_BYTES = 750_000
SKIPPED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".venv",
    "dist",
    "build",
    "coverage",
    "node_modules",
    "__pycache__",
}
SKIPPED_FILENAMES = {
    "license",
    "license.md",
    "license.txt",
    "copying",
    "copying.md",
    "copying.txt",
    "notice",
    "notice.md",
    "notice.txt",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "cargo.lock",
    "go.sum",
    "composer.lock",
    "pull_request_template.md",
    ".ds_store",
}
SKIPPED_PATH_PARTS = {
    "vendor",
    "tmp",
    "temp",
    "logs",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".devcontainer",
    "issue_template",
}
SKIPPED_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".tar", ".mp4", ".mov", ".mp3", ".woff", ".woff2", ".ttf", ".eot", ".lock",
    ".map", ".min.js", ".min.css", ".svg", ".csv", ".xlsx", ".db", ".sqlite", ".sqlite3",
}
ALLOWED_SUFFIXES = {
    ".md", ".mdx", ".rst", ".txt",
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".go", ".rs", ".java", ".cs", ".php", ".rb",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml",
    ".env.example", ".dockerfile",
}
ALLOWED_FILENAMES = {
    "dockerfile",
    "makefile",
    "readme",
    "readme.md",
    ".env.example",
    ".gitignore",
}


def load_repository(repo_url: str) -> dict[str, Any]:
    owner, repo = parse_github_url(repo_url)
    branch = get_default_branch(owner, repo)
    archive_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
    files, filter_stats = load_zip_files(archive_url)

    return {
        "url": repo_url,
        "name": repo,
        "branch": branch,
        "files": files,
        "filter_stats": filter_stats,
    }


def parse_github_url(repo_url: str) -> tuple[str, str]:
    parsed = urlparse(repo_url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]

    if parsed.netloc not in {"github.com", "www.github.com"} or len(parts) < 2:
        raise ValueError("Expected a GitHub URL like https://github.com/owner/repo")

    repo = parts[1].removesuffix(".git")
    return parts[0], repo


def get_default_branch(owner: str, repo: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_json(url)
    return data.get("default_branch") or "main"


def fetch_json(url: str) -> dict[str, Any]:
    import json

    request = build_request(url)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_zip_files(archive_url: str) -> tuple[list[dict[str, str]], dict[str, int]]:
    request = build_request(archive_url)
    with urlopen(request, timeout=60) as response:
        archive = response.read()

    files: list[dict[str, str]] = []
    stats = {
        "archive_entries": 0,
        "directories": 0,
        "oversized": 0,
        "filtered_paths": 0,
        "not_allowed": 0,
        "binary": 0,
        "decode_errors": 0,
        "included": 0,
    }

    with ZipFile(BytesIO(archive)) as zip_file:
        for info in zip_file.infolist():
            stats["archive_entries"] += 1

            if info.is_dir():
                stats["directories"] += 1
                continue

            if info.file_size > MAX_FILE_BYTES:
                stats["oversized"] += 1
                continue

            path_parts = info.filename.split("/")
            relative_path = "/".join(path_parts[1:])
            if not relative_path or should_skip_path(relative_path):
                stats["filtered_paths"] += 1
                continue

            if not is_allowed_path(relative_path):
                stats["not_allowed"] += 1
                continue

            raw = zip_file.read(info)
            if b"\x00" in raw[:2048]:
                stats["binary"] += 1
                continue

            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                stats["decode_errors"] += 1
                continue

            files.append({"path": relative_path, "content": content})
            stats["included"] += 1

    return files, stats


def should_skip_path(path: str) -> bool:
    parts = [part.lower() for part in path.split("/")]
    filename = parts[-1] if parts else ""

    if filename in SKIPPED_FILENAMES:
        return True

    if any(part in SKIPPED_DIRS or part in SKIPPED_PATH_PARTS for part in parts):
        return True

    lower = path.lower()
    return any(lower.endswith(suffix) for suffix in SKIPPED_SUFFIXES)


def is_allowed_path(path: str) -> bool:
    lower = path.lower()
    filename = lower.rsplit("/", 1)[-1]

    if filename in ALLOWED_FILENAMES:
        return True

    return any(lower.endswith(suffix) for suffix in ALLOWED_SUFFIXES)


def build_request(url: str) -> Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-rag-assistant",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return Request(url, headers=headers)
