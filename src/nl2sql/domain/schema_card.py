SCHEMA_CARD = """## 읽기 전용 테이블
departments(id, name, head_id); employees(id, name, dept_id, salary)
clients(id, name, industry, region, company_size, registered_at)
products(id, name, category, price_monthly, status)
contracts(id, client_id, product_id, manager_id, contract_type, amount, status)
projects(id, name, client_id, manager_id, contract_id, status, budget)
sales(id, contract_id, client_id, product_id, amount, sale_date, quarter, category, region)
support_tickets(id, client_id, product_id, assignee_id, priority, status, created_at, resolved_at)

값: category=cloud|security|data|consulting; region=서울|경기|부산|대전|대구|인천|광주|제주
미해결 티켓은 status IN ('open','in_progress'). sales.region/category/quarter는 직접 필터한다.
단일 SELECT만 출력하고 설명, 주석, 마크다운을 쓰지 않는다."""
