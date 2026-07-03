"""F12-E2B3K — qmark_sql_text helper."""
from sqlalchemy.sql.elements import TextClause

from app.infrastructure.database.query_helpers import qmark_sql_text


def test_qmark_sql_text_converts_positional_placeholders():
    clause = qmark_sql_text(
        "SELECT 1 WHERE a = ? AND b = ?",
        (10, "x"),
    )
    assert isinstance(clause, TextClause)
    assert ":p0" in str(clause)
    assert ":p1" in str(clause)


def test_qmark_sql_text_no_params():
    clause = qmark_sql_text("SELECT 1")
    assert isinstance(clause, TextClause)
