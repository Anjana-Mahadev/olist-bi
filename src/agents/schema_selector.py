from src.tools.sql_tools import format_schema_context, select_tables_for_question


def schema_selector_node(state: dict):
    selected_tables = select_tables_for_question(state.get("question", ""))
    return {
        **state,
        "selected_tables": selected_tables,
        "selected_schema": format_schema_context(selected_tables),
    }