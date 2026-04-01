from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict, total=False):
    request_id: str
    question: str
    intent: str
    response_type: str
    messages: List[Dict[str, str]]
    selected_tables: List[str]
    selected_schema: str
    complexity: str
    plan: List[str]
    sub_questions: List[str]
    sql_query: str
    db_result: Dict[str, Any]
    analysis: str
    final_answer: str
    confidence: float
    validation_errors: List[str]
    execution_error: str
    needs_clarification: bool
    retry_count: int
    max_retries: int
    data_results: List[Dict[str, Any]]
    node_trace: List[Dict[str, Any]]
    is_complete: bool