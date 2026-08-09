# MCP CompanyX

시스템 설계서의 네 모듈을 계약 우선·레이어드 아키텍처로 구현한 Python 프로젝트입니다.

- `vector`: 문서 청킹, 문맥 보강, RRF 하이브리드 검색
- `nl2sql`: 스키마 기반 SQL 생성, 읽기 전용 Guard, 실행
- `kg`: 온톨로지, 엔터티 해소, 제한된 그래프 탐색
- `router`: 규칙 기반 라우팅, TACC 컨텍스트 구성, 오케스트레이션

```bash
python -m pip install -e '.[test]'
pytest
python -m adapters.mcp_sdk_server
```

운영 조정값은 `TOP_K`와 `TAU` 두 개뿐입니다. PostgreSQL과 Ollama 연결 정보는 환경 변수 `PG_DSN`, `OLLAMA_URL`로 제공합니다.

