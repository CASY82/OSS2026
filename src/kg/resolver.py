import re
import unicodedata
from contracts.resolver import Resolution
from .repository import KgRepository

def normalize(text: str) -> str: return " ".join(unicodedata.normalize("NFKC", text).strip().lower().split())
class KgEntityResolver:
    TRGM_THRESHOLD = 0.45
    ENTITY_PATTERN = re.compile(r"\b(?:Client|Product)-[A-Z0-9]+\b", re.I)
    def __init__(self, repo: KgRepository, aliases: dict[str,str] | None = None): self.repo, self.aliases = repo, {normalize(k):v for k,v in (aliases or {}).items()}
    def resolve(self, text: str) -> Resolution:
        value = normalize(text)
        node = self.repo.exact_by_name(value)
        if node: return Resolution(str(node["node_id"]), str(node["name"]), str(node["node_type"]), 1.0, "exact")
        if value in self.aliases:
            node = self.repo.by_id(self.aliases[value])
            if node: return Resolution(str(node["node_id"]),str(node["name"]),str(node["node_type"]),.95,"alias")
        candidates = self.repo.trigram_top(value,3)
        if candidates and float(candidates[0].get("sim",0)) >= self.TRGM_THRESHOLD:
            node=candidates[0]; return Resolution(str(node["node_id"]),str(node["name"]),str(node["node_type"]),float(node["sim"]),"fuzzy")
        return Resolution(None,None,None,0.0,"not_found",[str(row["name"]) for row in candidates])
    def find_all(self, question: str) -> list[Resolution]: return [self.resolve(m.group(0)) for m in self.ENTITY_PATTERN.finditer(question)]
