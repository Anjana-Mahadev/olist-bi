import os
import re
import json
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "conversations.jsonl")

# Patterns to mask in log output
_PII_PATTERNS = [
    (re.compile(r'\b\d{5}[\-]?\d{3}\b'), '[ZIP_REDACTED]'),          # Brazilian CEP
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
]


def _mask_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def log_interaction(question, sql_query, db_result, final_answer):
    """
    Appends a single interaction to a JSONL log file with PII masking.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": _mask_pii(str(question)),
        "generated_sql": str(sql_query),
        "row_count": len(db_result.get("rows", [])) if isinstance(db_result, dict) else 0,
        "final_answer": _mask_pii(str(final_answer)),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")