import os
import time
import uuid
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from src.config import get_settings
from src.graph import app as langgraph_app
from src.logger import log_interaction

load_dotenv()
settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
flask_app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB max request size

# --- CORS ---
CORS(flask_app, origins=settings.CORS_ORIGINS.split(","))

# --- Rate Limiting ---
limiter = Limiter(get_remote_address, app=flask_app, default_limits=[settings.RATE_LIMIT])


def _require_api_key():
    """Return an error response if API_KEY is configured and the request doesn't match."""
    configured_key = settings.API_KEY
    if not configured_key:
        return None  # auth disabled
    provided = request.headers.get("X-API-Key", "")
    if provided != configured_key:
        return jsonify({"status": "error", "error": "Unauthorized"}), 401
    return None


# --- Health Check ---
@flask_app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


@flask_app.route('/')
def index():
    return render_template('index.html')


@flask_app.route('/query', methods=['POST'])
@limiter.limit(settings.RATE_LIMIT)
def query():
    auth_error = _require_api_key()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    user_question = data.get('question', '').strip()
    request_id = str(uuid.uuid4())[:8]

    if not user_question:
        return jsonify({"status": "error", "error": "Question cannot be empty"}), 400

    if len(user_question) > settings.MAX_QUESTION_LENGTH:
        return jsonify({
            "status": "error",
            "error": f"Question exceeds maximum length of {settings.MAX_QUESTION_LENGTH} characters"
        }), 400

    try:
        start_time = time.time()
        initial_state = {
            "request_id": request_id,
            "question": user_question,
            "messages": [{"role": "user", "content": user_question}],
            "plan": [],
            "data_results": [],
            "node_trace": [],
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": 2,
            "is_complete": False,
        }


        final_state = langgraph_app.invoke(initial_state)
        execution_time = round(time.time() - start_time, 2)

        analysis_text = final_state.get("final_answer") or final_state.get("analysis", "")
        if not isinstance(analysis_text, str):
            analysis_text = str(analysis_text)

        sql_query = final_state.get("sql_query", "") if final_state.get("intent") == "data" else ""

        # --- Metrics ---
        metrics = {
            "validation_errors": final_state.get("validation_errors", []),
            "repair_attempts": final_state.get("retry_count", 0),
            "max_retries": final_state.get("max_retries", 2),
            "confidence": final_state.get("confidence", None),
            "execution_error": final_state.get("execution_error", ""),
            "llm_tokens": final_state.get("llm_tokens", None),
            "llm_model": final_state.get("llm_model", None),
        }

        log_interaction(
            question=user_question,
            sql_query=sql_query,
            db_result=final_state.get("db_result", {}),
            final_answer=analysis_text,
        )

        return jsonify({
            "status": "success",
            "request_id": final_state.get("request_id", request_id),
            "sql": str(sql_query),
            "analysis": analysis_text,
            "execution_time": execution_time,
            "trace": final_state.get("node_trace", []),
            "metrics": metrics,
        })

    except Exception as e:
        logger.error(f"Error processing request {request_id}: {e}", exc_info=True)
        return jsonify({"status": "error", "request_id": request_id, "error": "Internal server error"}), 500

if __name__ == '__main__':
    flask_app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)