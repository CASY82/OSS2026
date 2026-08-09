from typing import Mapping
from .chunker import Section

def enrich(section: Section, metadata: Mapping[str, object]) -> str:
    header = " | ".join(f"{key}={value}" for key, value in metadata.items() if value not in (None, ""))
    return f"[{header}]\n## {section.title}\n{section.body.strip()}" if header else f"## {section.title}\n{section.body.strip()}"
