from contextlib import nullcontext
from contracts.infra import LlmError
class FakeDb:
    def __init__(self,dict_rows=None):self.dict_rows=dict_rows or []
    def fetch_dicts(self,sql,params=()):return list(self.dict_rows)
    def fetch(self,sql,params=()):return [tuple(row.values()) for row in self.dict_rows]
class FakeLlm:
    def __init__(self,generations=None,fail_embed=False):self.generations=list(generations or ["SELECT id FROM clients"]);self.fail_embed=fail_embed
    def embed(self,text,*,kind):
        if self.fail_embed:raise LlmError("offline")
        return [0.0]*768
    def generate(self,prompt,**kwargs):return self.generations.pop(0)
class FakeTracer:
    def span(self,name,**attrs):return nullcontext()
