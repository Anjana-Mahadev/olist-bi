from src.database import execute_query


def db_executor_node(state: dict):
    db_result = execute_query(state.get("sql_query", ""))
    execution_error = db_result.get("error", "") if isinstance(db_result, dict) else "Unknown database error."

    return {
        **state,
        "db_result": db_result,
        "execution_error": execution_error,
    }


def route_after_execution(state: dict):
    if not state.get("execution_error"):
        return "analyze"
    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "repair"
    return "fail"