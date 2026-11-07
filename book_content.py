from pathlib import Path
from functools import lru_cache
from import_books import split_pages

ROOT = Path(__file__).parent / "book_texts"

@lru_cache(maxsize=32)
def pages(title, author):
    path = ROOT / f"{title}|{author}.txt"
    if not path.exists():
        return []
    return split_pages(path.read_text(encoding="utf-8"))
