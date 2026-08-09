from dataclasses import dataclass, replace

MIN_CHARS = 80

@dataclass(frozen=True)
class Section:
    title: str
    body: str

def split_by_h2(markdown: str) -> list[Section]:
    parts: list[Section] = []
    current: Section | None = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            if current is not None:
                parts.append(current)
            current = Section(line[3:].strip(), "")
        elif current is not None:
            current = replace(current, body=current.body + line + "\n")
    if current is not None:
        parts.append(current)
    return merge_short(parts, MIN_CHARS)

def merge_short(sections: list[Section], min_chars: int = MIN_CHARS) -> list[Section]:
    out: list[Section] = []
    for section in sections:
        if out and len(section.body.strip()) < min_chars:
            prior = out[-1]
            out[-1] = replace(prior, body=prior.body + f"\n### {section.title}\n{section.body}")
        else:
            out.append(section)
    return out
