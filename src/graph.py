# src/graph.py
from langgraph.graph import StateGraph
from src.state import AgentState
from src.agents.orchestrator import orchestrator_node

graph = StateGraph(AgentState)
graph.add_node("orchestrator", orchestrator_node)
graph.set_entry_point("orchestrator")
app = graph.compile()