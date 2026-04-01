# src/graph.py
import time

from langgraph.graph import END, StateGraph
from src.state import AgentState
from src.agents.analyst_worker import analyst_node
from src.agents.answer_composer import answer_composer_node
from src.agents.db_executor import db_executor_node, route_after_execution
from src.agents.planner_worker import decomposer_node, planner_node, route_after_planning
from src.agents.router_worker import responder_node, route_after_routing, router_node
from src.agents.schema_selector import schema_selector_node
from src.agents.sql_validator import route_after_validation, sql_validator_node
from src.agents.sql_worker import repair_sql_node, sql_worker_node


def _timed_node(node_name, node_fn):
	def _wrapper(state: dict):
		start = time.perf_counter()
		next_state = node_fn(state)
		elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

		# Keep cumulative trace for the current request.
		existing_trace = next_state.get("node_trace", state.get("node_trace", []))
		trace = list(existing_trace) if isinstance(existing_trace, list) else []
		trace.append({"node": node_name, "ms": elapsed_ms})

		return {
			**next_state,
			"node_trace": trace,
		}

	return _wrapper

graph = StateGraph(AgentState)
graph.add_node("router", _timed_node("router", router_node))
graph.add_node("responder", _timed_node("responder", responder_node))
graph.add_node("schema_selector", _timed_node("schema_selector", schema_selector_node))
graph.add_node("planner", _timed_node("planner", planner_node))
graph.add_node("decomposer", _timed_node("decomposer", decomposer_node))
graph.add_node("sql_worker", _timed_node("sql_worker", sql_worker_node))
graph.add_node("sql_validator", _timed_node("sql_validator", sql_validator_node))
graph.add_node("repair_sql", _timed_node("repair_sql", repair_sql_node))
graph.add_node("db_executor", _timed_node("db_executor", db_executor_node))
graph.add_node("analyst", _timed_node("analyst", analyst_node))
graph.add_node("answer_composer", _timed_node("answer_composer", answer_composer_node))

graph.set_entry_point("router")
graph.add_conditional_edges("router", route_after_routing, {"respond": "responder", "data": "schema_selector"})
graph.add_edge("responder", "answer_composer")
graph.add_edge("schema_selector", "planner")
graph.add_conditional_edges("planner", route_after_planning, {"decompose": "decomposer", "sql": "sql_worker"})
graph.add_edge("decomposer", "sql_worker")
graph.add_edge("sql_worker", "sql_validator")
graph.add_conditional_edges(
	"sql_validator",
	route_after_validation,
	{"execute": "db_executor", "repair": "repair_sql", "fail": "answer_composer"},
)
graph.add_edge("repair_sql", "sql_validator")
graph.add_conditional_edges(
	"db_executor",
	route_after_execution,
	{"analyze": "analyst", "repair": "repair_sql", "fail": "answer_composer"},
)
graph.add_edge("analyst", "answer_composer")
graph.add_edge("answer_composer", END)

app = graph.compile()