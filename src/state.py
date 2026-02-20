from typing import TypedDict, Dict, Any


class AgentState(TypedDict):
    question: str
    sql_query: str
    db_result: Dict[str, Any]
    analysis: str