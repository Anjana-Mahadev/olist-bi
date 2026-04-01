from src.tools.sql_tools import validate_sql_query


def sql_validator_node(state: dict):
    validation_result = validate_sql_query(state.get("sql_query", ""), state.get("selected_tables", []))
    confidence = state.get("confidence", 0.7)
    if validation_result["valid"]:
        confidence = min(1.0, confidence + 0.05)

    return {
        **state,
        "sql_query": validation_result["sanitized_query"] or state.get("sql_query", ""),
        "validation_errors": validation_result["errors"],
        "confidence": confidence,
    }


def route_after_validation(state: dict):
    if not state.get("validation_errors"):
        return "execute"
    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "repair"
    return "fail"