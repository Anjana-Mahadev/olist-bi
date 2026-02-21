import os
import time
import logging
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from src.graph import app as langgraph_app
from src.logger import log_interaction

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/query', methods=['POST'])
def query():
    data = request.json
    user_question = data.get('question', '').strip()

    try:
        start_time = time.time()
        initial_state = {
            "question": user_question, 
            "messages": [{"role": "user", "content": user_question}],
            "plan": [],
            "data_results": [],
            "is_complete": False
        }

        # Invoke the graph
        final_state = langgraph_app.invoke(initial_state)
        execution_time = round(time.time() - start_time, 2)

        # 🔥 DEBUG PRINT: See exactly what the agents are returning in your terminal
        print("\n" + "="*50)
        print("DEBUG: FULL FINAL STATE RECEIVED FROM AGENTS")
        print(json.dumps({k: str(v) for k, v in final_state.items()}, indent=2))
        print("="*50 + "\n")

        # --- GREEDY EXTRACTION ---
        # 1. Try to find the insight in data_results list
        sql_query = "N/A"
        analysis_insight = ""
        
        results = final_state.get("data_results", [])
        for item in results:
            if isinstance(item, dict):
                if item.get("agent") == "sql_worker":
                    sql_query = item.get("raw_data", sql_query)
                if item.get("agent") == "analyst_worker":
                    analysis_insight = item.get("insight", "")

        # 2. FALLBACK: Check top-level keys if the agent didn't use data_results
        if not analysis_insight:
            analysis_insight = final_state.get("analysis") or \
                               final_state.get("final_answer") or \
                               final_state.get("insight") or \
                               "Agents finished, but no 'analysis' key was found in the state."

        if sql_query == "N/A":
            sql_query = final_state.get("sql_query") or "N/A"

        return jsonify({
            "status": "success",
            "sql": str(sql_query),
            "analysis": str(analysis_insight),
            "execution_time": execution_time
        })

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5000, debug=True)