from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.pg_models import Transaction, AuditLog


class PostgresRepository:

    def __init__(self, session: Session):
        self.session = session

    def get(self, request_id: str):
        return self.session.query(Transaction).filter_by(request_id=request_id).first()

    def find_by_status(self, statuses: list, limit: int = 100):
        return (
            self.session.query(Transaction)
            .filter(Transaction.status.in_(statuses))
            .limit(limit)
            .all()
        )

    def save(self, data: dict):
        tx = Transaction(**data)
        try:
            self.session.add(tx)
            self.session.commit()
            return tx
        except Exception:
            self.session.rollback()
            raise

    def update_with_version(self, request_id: str, values: dict, version: int):
        tx = self.session.query(Transaction).filter_by(request_id=request_id, version=version).first()
        if not tx:
            raise Exception("OPTIMISTIC_LOCK_FAILED")

        for k, v in values.items():
            setattr(tx, k, v)

        tx.version = tx.version + 1

        try:
            self.session.commit()
            return tx
        except Exception:
            self.session.rollback()
            raise


class AuditRepository:

    def __init__(self, session: Session):
        self.session = session

    def log(self, data: dict):
        audit = AuditLog(**data)
        try:
            self.session.add(audit)
            self.session.commit()
            return audit
        except Exception:
            self.session.rollback()
            raise
