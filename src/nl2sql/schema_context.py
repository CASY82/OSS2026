"""NL2SQL 프롬프트에 상시 주입되는 고정 컨텍스트.

ADR 결정사항 그대로 구현한다:
  1. 스키마 링킹 모듈 없이 8개 업무 테이블 DDL 전체를 상시 주입
  2. 한<->영 용어 매핑(glossary)을 정적 텍스트로 상시 주입
  3. 패턴이 겹치지 않는 few-shot 5개(집계(매출+분기 단독필터) / JOIN+GROUP BY+ORDER+LIMIT /
     날짜필터 / JOIN+GROUP BY+ORDER+LIMIT(다른 도메인) / 필터+목록)를 고정 포함.
     첫 번째(매출+분기 단독필터) 예시는 실측 테스트에서 "매출" 질문에 분기 필터가 붙으면
     sales 대신 contracts로 새는 실패가 관찰되어 넣은 것 — glossary 텍스트만으로는 안
     잡히던 유형이라 few-shot으로 보강함.

document_chunks 테이블(벡터 검색용)은 nl2sql 도구의 대상이 아니므로 제외한다.
"""

SCHEMA_DDL = """\
CREATE TABLE departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    head_id     INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- sql/01-schema.sql에서 ALTER TABLE로 선언된 관계
-- departments.head_id REFERENCES employees(id)

CREATE TABLE employees (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    position    VARCHAR(50) NOT NULL,
    dept_id     INTEGER NOT NULL REFERENCES departments(id),
    hire_date   DATE NOT NULL,
    salary      INTEGER NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE clients (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    industry        VARCHAR(50) NOT NULL,
    region          VARCHAR(30) NOT NULL,
    company_size    VARCHAR(20) NOT NULL,
    contact_name    VARCHAR(50),
    contact_email   VARCHAR(100),
    registered_at   DATE NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    description     TEXT,
    price_monthly   INTEGER NOT NULL,
    version         VARCHAR(20),
    release_date    DATE,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contracts (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    manager_id      INTEGER NOT NULL REFERENCES employees(id),
    contract_type   VARCHAR(20) NOT NULL,
    amount          INTEGER NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    manager_id      INTEGER NOT NULL REFERENCES employees(id),
    contract_id     INTEGER REFERENCES contracts(id),
    status          VARCHAR(20) DEFAULT 'in_progress',
    start_date      DATE NOT NULL,
    end_date        DATE,
    budget          INTEGER,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sales (
    id              SERIAL PRIMARY KEY,
    contract_id     INTEGER NOT NULL REFERENCES contracts(id),
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    amount          INTEGER NOT NULL,
    sale_date       DATE NOT NULL,
    quarter         VARCHAR(10) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    region          VARCHAR(30) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE support_tickets (
    id              SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    assignee_id     INTEGER REFERENCES employees(id),
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    priority        VARCHAR(10) NOT NULL,
    status          VARCHAR(20) DEFAULT 'open',
    created_at      TIMESTAMP NOT NULL,
    resolved_at     TIMESTAMP
);
"""

GLOSSARY = """\
- 매출 -> sales.amount
- 계약금액 -> contracts.amount
- 연봉 -> employees.salary
- 예산 -> projects.budget
- 고객사 -> clients
- 부서 -> departments
- 분기 -> sales.quarter (형식: 'YYYY-QN', 예: '2025-Q3')
- 활성 계약 -> contracts.status = 'active'
- 활성 제품 -> products.status = 'active'
- 진행 중 프로젝트 -> projects.status = 'in_progress'
- 활성 고객사/직원 -> clients.is_active / employees.is_active = TRUE
- 비활성 고객사/직원 -> clients.is_active / employees.is_active = FALSE
- 미해결 티켓 -> support_tickets.status IN ('open', 'in_progress')
- 우선순위(긴급/critical) -> support_tickets.priority

products.category / sales.category 값 (전부 영어 소문자로 저장됨):
- 보안(솔루션) -> 'security'
- 클라우드 -> 'cloud'
- 데이터(분석) -> 'data'
- 컨설팅 -> 'consulting'

support_tickets.priority 값 (전부 영어 소문자): 'critical', 'high', 'medium', 'low'
support_tickets.status 값 (전부 영어 소문자): 'open', 'in_progress', 'resolved', 'closed'

clients.company_size 값:
- 스타트업 -> 'startup'
- 중견 -> 'mid'
- 대기업 -> 'enterprise'

products.status 값:
- 활성 -> 'active'
- 베타 -> 'beta'

contracts.status 값:
- 활성 -> 'active'
- 완료 -> 'completed'
- 취소/해지 -> 'cancelled'

contracts.contract_type 값:
- 구독 -> 'subscription'
- 프로젝트형 계약 -> 'project'
- 유지보수 -> 'maintenance'

projects.status 값:
- 진행 중 -> 'in_progress'
- 계획 중 -> 'planning'
- 완료 -> 'completed'
- 보류 중 -> 'on_hold'

support_tickets.status 한국어 매핑:
- 열린/열림 -> 'open'
- 진행 중 -> 'in_progress'
- 해결된/해결됨 -> 'resolved'
- 종료된/닫힘 -> 'closed'
- 미해결 -> IN ('open', 'in_progress')
- "열린"은 오직 'open'만 뜻한다. 질문에 "미해결" 또는 "아직 해결되지 않은"이
  명시된 경우에만 IN ('open', 'in_progress')를 사용한다.

주의: category/priority/status 등 코드성 컬럼의 값은 대소문자를 포함해 위 표기와
정확히 일치해야 한다 (예: 'Critical'이 아니라 'critical'). 확신이 없으면 대소문자를
구분하지 않는 비교(예: LOWER(컬럼) = LOWER('값'))를 사용한다.
"""

DOMAIN_SEMANTICS = """\
Company-X 의미 매핑:

1. 중심 수치(metric)
- 매출/매출액: sales.amount. 기간은 sales.sale_date 또는 sales.quarter, 지역은 sales.region,
  카테고리는 sales.category를 우선 사용한다.
- 계약금액: contracts.amount. 제품별 계약금액은 contracts JOIN products 후 SUM(contracts.amount).
- 연봉: employees.salary. 부서별 평균 연봉은 employees JOIN departments 후 AVG(employees.salary).
- 예산: projects.budget.
- price_monthly는 제품 카탈로그 정가다. 매출/계약금액/연봉/예산을 대신하지 않는다.

2. 중심 엔티티(table)
- 고객사/고객: clients
- 직원/사원: employees
- 부서/팀: departments
- 제품/솔루션: products
- 계약: contracts
- 프로젝트: projects
- 티켓/장애/지원 요청: support_tickets

3. 문맥별 필터 컬럼
- 매출 문맥: 카테고리=sales.category, 분기=sales.quarter, 지역=sales.region
- 제품 문맥: 카테고리=products.category, 상태=products.status, 출시일=products.release_date
- 계약 문맥: 상태=contracts.status, 시작일=contracts.start_date, 종료일=contracts.end_date
- 프로젝트 문맥: 상태=projects.status, 시작일=projects.start_date, 종료일=projects.end_date
- 고객사 문맥: 지역=clients.region, 등록일=clients.registered_at, 활성=clients.is_active
- 직원 문맥: 부서=employees.dept_id로 departments.id와 JOIN, 입사일=employees.hire_date,
  활성=employees.is_active
- 티켓 문맥: 우선순위=support_tickets.priority, 상태=support_tickets.status,
  미해결=support_tickets.status IN ('open', 'in_progress')

4. 값 매핑
- 보안/보안 솔루션='security', 클라우드='cloud', 데이터/데이터 분석='data',
  컨설팅='consulting'
- Critical/긴급='critical'
- 미해결='open' 또는 'in_progress'
- 분기 값은 반드시 'YYYY-QN' 형식이다. 예: 2025년 3분기 -> '2025-Q3'
- 고객사 규모: 스타트업='startup', 중견='mid', 대기업='enterprise'
- 제품 상태: 활성='active', 베타='beta'
- 계약 상태: 활성='active', 완료='completed', 취소/해지='cancelled'
- 계약 유형: 구독='subscription', 프로젝트형 계약='project', 유지보수='maintenance'
- 프로젝트 상태: 진행 중='in_progress', 계획 중='planning', 완료='completed', 보류 중='on_hold'
- 티켓 상태: 열림='open', 진행 중='in_progress', 해결='resolved', 종료/닫힘='closed'

5. 모호성 해소 원칙
- 질문에 metric이 있으면 metric의 테이블이 중심 테이블이다. 예: "제품들의 매출"은
  products.price_monthly가 아니라 sales.amount를 집계한다.
- 이름을 출력해야 할 때만 중심 테이블에서 이름 테이블로 JOIN한다. 예: 고객사 이름은 clients,
  제품 이름은 products, 부서 이름은 departments에서 가져온다.
- "상위/큰 순서"가 metric과 함께 나오면 COUNT가 아니라 해당 metric의 SUM/AVG 등을 기준으로 정렬한다.
"""

FEW_SHOTS = [
    {
        # 매출+기간(분기) 단독 필터 — quarter 조건만 있어도 매출은 항상 sales 테이블
        # (contracts.start_date 등 다른 테이블의 날짜 컬럼으로 새지 않도록 하는 예시.
        # 실측 테스트에서 이 예시가 없으면 분기 필터가 붙은 매출 질문이 실패로 관찰됨)
        "question": "2026년 1분기 총 매출액은 얼마야?",
        "sql": "SELECT SUM(amount) AS total_amount FROM sales WHERE quarter = '2026-Q1';",
    },
    {
        "question": "부산 지역 매출 상위 3개 고객사를 알려줘",
        "sql": (
            "SELECT c.name, SUM(s.amount) AS total_amount "
            "FROM sales s JOIN clients c ON s.client_id = c.id "
            "WHERE s.region = '부산' "
            "GROUP BY c.name "
            "ORDER BY total_amount DESC "
            "LIMIT 3;"
        ),
    },
    {
        "question": "2025년에 등록된 고객사는 몇 개야?",
        "sql": (
            "SELECT COUNT(*) FROM clients "
            "WHERE registered_at BETWEEN '2025-01-01' AND '2025-12-31';"
        ),
    },
    {
        "question": "직원 수가 가장 많은 부서는 어디야?",
        "sql": (
            "SELECT d.name, COUNT(*) AS emp_count "
            "FROM employees e JOIN departments d ON e.dept_id = d.id "
            "GROUP BY d.name "
            "ORDER BY emp_count DESC "
            "LIMIT 1;"
        ),
    },
    {
        "question": "클라우드 솔루션 카테고리 제품들의 월 평균 매출은?",
        "sql": "SELECT AVG(amount) AS avg_amount FROM sales WHERE category = 'cloud';",
    },
    {
        "question": "현재 활성 상태인 계약 수는 몇 개야?",
        "sql": "SELECT COUNT(*) FROM contracts WHERE status = 'active';",
    },
    {
        "question": "Critical 우선순위 티켓 중 아직 해결되지 않은 건은?",
        "sql": (
            "SELECT title, description, priority, status "
            "FROM support_tickets "
            "WHERE priority = 'critical' AND status IN ('open', 'in_progress');"
        ),
    },
    {
        "question": "열린 티켓은 몇 건이야?",
        "sql": "SELECT COUNT(*) FROM support_tickets WHERE status = 'open';",
    },
    {
        "question": "영업팀 직원 목록을 알려줘",
        "sql": (
            "SELECT e.name, e.position "
            "FROM employees e JOIN departments d ON e.dept_id = d.id "
            "WHERE d.name = '영업팀';"
        ),
    },
]


def _format_few_shots() -> str:
    blocks = []
    for i, ex in enumerate(FEW_SHOTS, start=1):
        blocks.append(f"예시 {i}\n질문: {ex['question']}\nSQL: {ex['sql']}")
    return "\n\n".join(blocks)


SQL_SYNTAX_RULES = """\
- GROUP BY를 쓰는 경우, SELECT/ORDER BY에 등장하는 컬럼 중 GROUP BY에 없는 컬럼은
  반드시 SUM/AVG/COUNT/MAX/MIN 등 집계 함수로 감싼다. 원본 컬럼(예: e.salary)을
  집계 함수 없이 그대로 SELECT나 ORDER BY에 쓰지 않는다.
- 집계 결과(SUM/AVG/COUNT 등)에 조건을 걸 때는 WHERE가 아니라 HAVING을 쓴다.
  개별 행에 대한 조건은 WHERE, 그룹핑 후 집계값에 대한 조건은 HAVING이다.
- 두 개 이상의 테이블을 조인할 때는 각 테이블에 짧은 별칭(alias)을 붙이고,
  모든 컬럼 참조 앞에 그 별칭을 명시한다(예: e.name, d.name처럼 구분).
- 날짜/기간 조건은 'YYYY-MM-DD' 형식 문자열과 BETWEEN을 사용하고, 컬럼이
  DATE인지 TIMESTAMP인지에 따라 시간 포함 여부를 함께 고려한다.
- 연도만 주어진 경우 quarter에 'YYYY-Q' 또는 'YYYY-Q*' 같은 값을 만들지 않는다.
  해당 엔티티의 날짜 컬럼을 사용해 `>= 'YYYY-01-01' AND < '다음연도-01-01'`로 필터링한다.
  매출=sales.sale_date, 계약=contracts.start_date, 프로젝트=projects.start_date,
  제품 출시=products.release_date, 고객 등록=clients.registered_at,
  직원 입사=employees.hire_date, 티켓 생성=support_tickets.created_at을 사용한다.
- 분기가 명시된 매출 질문에만 sales.quarter = 'YYYY-QN'을 사용한다.
- 전체 행 개수는 COUNT(*), 특정 컬럼의 NULL이 아닌 값 개수만 셀 때는
  COUNT(컬럼명)을 구분해서 쓴다.
- 매출 합계/평균/최대/최소는 sales.amount를 사용하지만, "매출 건수"는
  sales 테이블에서 COUNT(*) 또는 COUNT(sales.id)를 사용한다.
- 정렬 후 상위/하위 N개만 필요하면 ORDER BY ... LIMIT N을 쓴다. 집계값 기준으로
  정렬할 때는 SELECT에 준 별칭 또는 집계식 자체를 ORDER BY에 사용한다.
- NULL 여부 비교는 `= NULL`이 아니라 `IS NULL` / `IS NOT NULL`을 사용한다.
"""


REVENUE_TABLE_RULE = """\
질문에 "매출"이라는 단어가 있으면 아래 순서를 그대로 따른다:
1. FROM 절은 무조건 sales 테이블로 시작한다. products나 contracts로 시작하지 않는다.
2. "카테고리" 필터는 sales.category, "분기"는 sales.quarter, "지역"은 sales.region으로 건다.
   products.category나 contracts의 날짜 컬럼으로 대체하지 않는다.
3. 질문의 문법적 주어가 "제품(들)"이어도 무시한다 — products 테이블을 쓰지 않는다.
   products.price_monthly는 카탈로그 정가일 뿐 실제 매출이 아니다. 실제 매출 금액은
   sales.amount에만 있다.
4. 제품명이나 고객사명을 함께 보여줘야 할 때만 sales를 products/clients와 JOIN한다.
"""


def build_system_context() -> str:
    """LLM에 매 호출마다 그대로 주입하는 고정 컨텍스트 문자열."""
    return (
        "당신은 PostgreSQL 전문가입니다. 아래 스키마와 용어 사전, SQL 문법 규칙, "
        "예시를 참고하여 사용자의 자연어 질문에 대응하는 SQL 쿼리 단 하나만 생성하세요.\n\n"
        "출력 형식 규칙:\n"
        "- SELECT 문만 작성한다 (INSERT/UPDATE/DELETE/DDL 금지)\n"
        "- 세미콜론으로 끝나는 SQL 문장 하나만 출력한다\n"
        "- 설명, 마크다운 코드블록, 주석 없이 SQL 텍스트만 출력한다\n"
        "- 스키마에 없는 테이블/컬럼을 만들어내지 않는다\n\n"
        f"[스키마]\n{SCHEMA_DDL}\n"
        f"[용어 사전]\n{GLOSSARY}\n"
        f"[Company-X 도메인 의미 매핑]\n{DOMAIN_SEMANTICS}\n"
        f"[SQL 문법 규칙]\n{SQL_SYNTAX_RULES}\n"
        f"[예시]\n{_format_few_shots()}\n\n"
        f"[매출 질문 처리 규칙 — 반드시 지킬 것]\n{REVENUE_TABLE_RULE}\n"
    )
