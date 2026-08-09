from contracts.infra import Db
class SqlRepository:
    def __init__(self, db: Db): self.db = db
    def execute(self, sql: str) -> tuple[list[list[object]], list[str]]:
        rows = self.db.fetch_dicts(sql)
        columns = list(rows[0]) if rows else []
        return [[row.get(column) for column in columns] for row in rows], columns
