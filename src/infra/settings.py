from dataclasses import dataclass
import os
@dataclass(frozen=True)
class Settings:
    TOP_K:int=5
    TAU:float=.55
    PG_DSN:str="postgresql://mcp_reader:mcp_reader@localhost:5432/companyx"
    OLLAMA_URL:str="http://localhost:11434"
    GENERATE_MODEL:str="gemma4:e4b"
    EMBED_MODEL:str="nomic-embed-text:latest"
    @classmethod
    def from_env(cls):
        return cls(
            TOP_K=int(os.getenv("TOP_K","5")),
            TAU=float(os.getenv("TAU",".55")),
            PG_DSN=os.getenv("PG_DSN",cls.PG_DSN),
            OLLAMA_URL=os.getenv("OLLAMA_URL",cls.OLLAMA_URL),
            GENERATE_MODEL=os.getenv("GENERATE_MODEL",cls.GENERATE_MODEL),
            EMBED_MODEL=os.getenv("EMBED_MODEL",cls.EMBED_MODEL),
        )
