from pathlib import Path


def parse_text(file_path: str) -> dict:
    text = Path(file_path).read_text(
        encoding="utf-8",
        errors="ignore",
    )

    return {
        "text": text,
        "character_count": len(text),
        "line_count": len(text.splitlines()),
    }