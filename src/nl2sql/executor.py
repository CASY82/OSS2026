"""가드레일을 통과한 SQL을 PostgreSQL에서 실행한다."""

import os

import psycopg2

from .config import load_dotenv

load_dotenv()

PG_DSN = os.environ.get("PG_DSN")
PG_HOST = os.environ.get("PGHOST", "localhost")
PG_PORT = os.environ.get("PGPORT", "5432")
PG_DATABASE = os.environ.get("PGDATABASE", "companyx")
PG_USER = os.environ.get("PGUSER", "postgres")
PG_PASSWORD = os.environ.get("PGPASSWORD", "")


def _connect():
    if PG_DSN:
        conn = psycopg2.connect(PG_DSN)
    else:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD,
        )
    # 가드레일(guardrail.py)과 별개로 DB 세션 자체를 읽기 전용으로 고정해
    # 쓰기 차단을 이중으로 보장한다.
    conn.set_session(readonly=True, autocommit=True)
    return conn


def run(sql: str) -> dict:
    """SQL을 실행하고 결과를 반환한다.

    예외를 전파하지 않고 {"error": "..."} 형태로 감싸서 반환한다 —
    호출부(service.py)가 이 에러 메시지를 그대로 재시도 프롬프트에 넣는다.
    """
    try:
        conn = _connect()
    except psycopg2.Error as exc:
        return {"error": f"DB 연결 실패: {exc}"}

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description is None:
                return {"columns": [], "rows": []}
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return {"columns": columns, "rows": rows}
    except psycopg2.Error as exc:
        return {"error": str(exc)}
    finally:
        conn.close()
