from sqlalchemy import text
from sqlalchemy.orm import Session


def test_database_session_executes_query(db_session: Session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar_one() == 1
