def infer_language_from_path(path: str) -> str | None:
    if "." not in path:
        return None
    return path.rsplit(".", 1)[-1].lower()