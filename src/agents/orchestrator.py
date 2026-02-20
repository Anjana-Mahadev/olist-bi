# src/agents/orchestrator.py
from src.agents.sql_worker import SQLWorker
from src.agents.analyst_worker import AnalystWorker

sql_worker = SQLWorker()
analyst_worker = AnalystWorker()

def orchestrator_node(state: dict):
    print("\n🧠 Generating SQL...")
    state = sql_worker.run(state)
    print("Generated SQL:\n", state["sql_query"])

    print("\n📊 Running Analysis...")
    state = analyst_worker.run(state)
    print("✅ Done.")

    return state