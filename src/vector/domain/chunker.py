from dataclasses import dataclass, replace

MIN_CHARS = 80

@dataclass(frozen=True)
class Section:
    title: str
    body: str

def split_by_h2(markdown: str) -> list[Section]:
    """Split a document into one overview chunk and one chunk per H2 section.

    CompanyX has 40 document headings and 162 H2 sections, producing the
    dataset contract's 202 stable semantic chunks. Context enrichment makes
    even short sections independently searchable, so sections are not merged.
    """
    parts: list[Section] = []
    current: Section | None = None
    preamble: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if current is not None:
                parts.append(current)
            current = Section(line[3:].strip(), "")
        elif current is not None:
            current = replace(current, body=current.body + line + "\n")
        else:
            preamble.append(line)
    if current is not None:
        parts.append(current)
    heading = next((line[2:].strip() for line in preamble if line.startswith("# ")), "문서 개요")
    overview = Section(heading, "\n".join(preamble).strip())
    return [overview, *parts] if overview.body else parts

def merge_short(sections: list[Section], min_chars: int = MIN_CHARS) -> list[Section]:
    out: list[Section] = []
    for section in sections:
        if out and len(section.body.strip()) < min_chars:
            prior = out[-1]
            out[-1] = replace(prior, body=prior.body + f"\n### {section.title}\n{section.body}")
        else:
            out.append(section)
    return out
