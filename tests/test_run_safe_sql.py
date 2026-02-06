import pytest
from src.genai_sql_engine import run_safe_sql

# -------------------------
# MOCKS (fake functions)
# -------------------------

def fake_generate_sql(prompt, schema, question):
    return "SELECT 1 AS test_col;"

def fake_execute_sql(sql):
    return ["test_col"], [(1,)]

def fake_retry_with_error(prompt, schema, question, error):
    return "SELECT 2 AS test_col;"

# -------------------------
# TEST 1: Happy path
# -------------------------

def test_run_safe_sql_success(monkeypatch):
    monkeypatch.setattr(
        "src.genai_sql_engine.generate_sql",
        fake_generate_sql
    )
    monkeypatch.setattr(
        "src.genai_sql_engine.execute_sql",
        fake_execute_sql
    )

    sql, cols, rows = run_safe_sql(
        prompt="",
        schema="",
        question="simple test"
    )

    assert sql.strip().startswith("SELECT")
    assert cols == ["test_col"]
    assert rows == [(1,)]

# -------------------------
# TEST 2: Retry logic works
# -------------------------

def test_run_safe_sql_retry(monkeypatch):
    calls = {"count": 0}

    def failing_execute_sql(sql):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("SQL error")
        return ["test_col"], [(2,)]

    monkeypatch.setattr(
        "src.genai_sql_engine.generate_sql",
        fake_generate_sql
    )
    monkeypatch.setattr(
        "src.genai_sql_engine.execute_sql",
        failing_execute_sql
    )
    monkeypatch.setattr(
        "src.genai_sql_engine.retry_with_error",
        fake_retry_with_error
    )

    sql, cols, rows = run_safe_sql(
        prompt="",
        schema="",
        question="retry test",
        max_retries=1
    )

    assert rows == [(2,)]
    assert calls["count"] == 2

# -------------------------
# TEST 3: Retry limit enforced
# -------------------------

def test_run_safe_sql_retry_limit(monkeypatch):
    def always_fail(sql):
        raise RuntimeError("Always fails")

    monkeypatch.setattr(
        "src.genai_sql_engine.generate_sql",
        fake_generate_sql
    )
    monkeypatch.setattr(
        "src.genai_sql_engine.execute_sql",
        always_fail
    )
    monkeypatch.setattr(
        "src.genai_sql_engine.retry_with_error",
        fake_retry_with_error
    )

    with pytest.raises(RuntimeError):
        run_safe_sql(
            prompt="",
            schema="",
            question="fail test",
            max_retries=1
        )
