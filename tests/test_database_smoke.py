import sqlite3

from src import database


def test_execute_query_returns_rows_and_columns(tmp_path, monkeypatch):
    db_file = tmp_path / "test_olist.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE metrics (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO metrics VALUES (1, 'orders')")
    conn.commit()
    conn.close()

    result = database.execute_query("SELECT id, name FROM metrics")

    assert "error" not in result
    assert result["columns"] == ["id", "name"]
    assert result["rows"] == [(1, "orders")]


def test_execute_query_returns_error_for_invalid_sql(tmp_path, monkeypatch):
    db_file = tmp_path / "test_olist.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    result = database.execute_query("SELECT * FROM does_not_exist")

    assert "error" in result
    assert "no such table" in result["error"].lower()
