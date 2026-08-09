from dataclasses import dataclass
import os
@dataclass(frozen=True)
class Settings:
    TOP_K:int=5; TAU:float=.55; PG_DSN:str="postgresql://mcp_reader:mcp_reader@localhost:5432/companyx"; OLLAMA_URL:str="http://localhost:11434"
    @classmethod
    def from_env(cls): return cls(int(os.getenv("TOP_K","5")),float(os.getenv("TAU",".55")),os.getenv("PG_DSN",cls.PG_DSN),os.getenv("OLLAMA_URL",cls.OLLAMA_URL))
