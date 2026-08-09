import re

PATTERNS = {
    "client": re.compile(r"\bClient-[A-Z0-9]+\b", re.I),
    "product": re.compile(r"\bProduct-[A-Z0-9]+\b", re.I),
    "date": re.compile(r"\b20\d{2}[-./]\d{1,2}[-./]\d{1,2}\b"),
}

def extract(text: str) -> dict[str, list[str]]:
    return {key: list(dict.fromkeys(match.group(0) for match in pattern.finditer(text))) for key, pattern in PATTERNS.items()}
