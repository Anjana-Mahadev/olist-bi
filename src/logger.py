import os
import json
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "conversations.jsonl")


def log_interaction(question, sql_query, db_result, final_answer):
    """
    Appends a single interaction to a JSONL log file.
    """

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "generated_sql": sql_query,
        "db_result": db_result,
        "final_answer": final_answer
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")