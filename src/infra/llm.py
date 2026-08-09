from contracts.infra import LlmError,LlmTimeout
class OllamaClient:
    EMBED_DIM=768
    def __init__(self,base_url:str,generate_model:str="gemma4:e2b",embed_model:str="nomic-embed-text"):self.base_url,self.generate_model,self.embed_model=base_url.rstrip("/"),generate_model,embed_model
    def embed(self,text:str,*,kind:str):
        prefix="search_document: " if kind=="document" else "search_query: "
        try:
            import httpx
            response=httpx.post(f"{self.base_url}/api/embed",json={"model":self.embed_model,"input":prefix+text},timeout=30);response.raise_for_status();vector=response.json()["embeddings"][0]
            if len(vector)!=self.EMBED_DIM:raise LlmError(f"embedding dimension {len(vector)} != {self.EMBED_DIM}")
            return vector
        except LlmError:raise
        except Exception as exc:raise LlmError(str(exc)) from exc
    def generate(self,prompt:str,*,stop=None,max_tokens=300,timeout_s=30):
        try:
            import httpx
            response=httpx.post(f"{self.base_url}/api/generate",json={"model":self.generate_model,"prompt":prompt,"stream":False,"options":{"temperature":0,"num_predict":max_tokens,"stop":stop or []}},timeout=timeout_s);response.raise_for_status();return response.json()["response"].strip()
        except TimeoutError as exc:raise LlmTimeout(str(exc)) from exc
        except Exception as exc:raise LlmError(str(exc)) from exc
