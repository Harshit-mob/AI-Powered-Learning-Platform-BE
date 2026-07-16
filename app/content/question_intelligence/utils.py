from functools import lru_cache
from .constants import PUNCTUATION_REGEX

@lru_cache(maxsize=4096)
def normalize_text(text: str) -> str:
    """Normalizes text by removing punctuation and converting to lowercase."""
    if not text:
        return ""
    return " ".join(PUNCTUATION_REGEX.sub('', text).lower().split())

@lru_cache(maxsize=4096)
def count_words(text: str) -> int:
    """Returns the word count of a normalized text."""
    if not text:
        return 0
    return len(normalize_text(text).split())
