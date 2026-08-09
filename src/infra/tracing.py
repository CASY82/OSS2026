from contextlib import contextmanager
from datetime import datetime,timezone
import json,time
class JsonlTracer:
    def __init__(self,path):self.path=path
    @contextmanager
    def span(self,name,**attrs):
        started=time.perf_counter();error=None
        try:yield
        except Exception as exc:error=type(exc).__name__;raise
        finally:
            record={"timestamp":datetime.now(timezone.utc).isoformat(),"name":name,"elapsed_ms":int((time.perf_counter()-started)*1000),"error":error,**attrs}
            with open(self.path,"a",encoding="utf-8") as file:file.write(json.dumps(record,ensure_ascii=False)+"\n")
