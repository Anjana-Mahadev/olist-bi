from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import get_settings
from src.tools.sql_tools import format_schema_context
from src.agents.llm_utils import safe_invoke

class SQLWorker:
    def __init__(self):
        self.llm = None

    def _get_llm(self):
        if self.llm is None:
            settings = get_settings()
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0,
            )
        return self.llm

    def _build_prompt(self, state: dict) -> str:
        schema_context = state.get("selected_schema") or format_schema_context(state.get("selected_tables", []))
        plan = state.get("plan", [])
        sub_questions = state.get("sub_questions", [])
        validation_errors = state.get("validation_errors", [])
        execution_error = state.get("execution_error", "")
        previous_sql = state.get("sql_query", "")

        plan_text = "\n".join(f"- {step}" for step in plan) if plan else "- Answer the question with one SQLite query"
        sub_question_text = "\n".join(f"- {item}" for item in sub_questions) if sub_questions else "- None"

        repair_block = ""
        if validation_errors or execution_error or previous_sql:
            repair_lines = []
            if previous_sql:
                repair_lines.append(f"Previous SQL:\n{previous_sql}")
            if validation_errors:
                repair_lines.append("Validation issues:\n" + "\n".join(f"- {item}" for item in validation_errors))
            if execution_error:
                repair_lines.append(f"Execution error:\n- {execution_error}")
            repair_block = "\n\nFix the issues below when generating the next SQL query:\n" + "\n".join(repair_lines)

        return f"""
You are an expert SQLite analyst for the Olist e-commerce database.

Rules:
- Return exactly one read-only SQLite query.
- Use only the tables and columns listed below.
- Do not use markdown, explanations, or code fences.
- Prefer explicit joins and explicit column names.
- For row-level queries, include a LIMIT clause.

Available schema:
{schema_context}

User question:
{state.get('question', '')}

Planning notes:
{plan_text}

Sub-questions:
{sub_question_text}
{repair_block}
""".strip()

    def run(self, state: dict):
        prompt = self._build_prompt(state)
        llm = self._get_llm()
        response = safe_invoke(llm, [HumanMessage(content=prompt)], timeout_seconds=35)
        sql_query = response.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # Track LLM model and token usage if available
        llm_model = getattr(llm, "model_name", None)
        llm_tokens = None
        # Try to extract token usage from response (LangChain convention)
        if hasattr(response, "usage") and response.usage:
            # OpenAI-like usage dict
            llm_tokens = response.usage.get("total_tokens")
        elif hasattr(response, "token_usage"):
            llm_tokens = response.token_usage

        return {
            **state,
            "sql_query": sql_query,
            "validation_errors": [],
            "execution_error": "",
            "llm_model": llm_model,
            "llm_tokens": llm_tokens,
        }


_sql_worker = SQLWorker()


def sql_worker_node(state: dict):
    return _sql_worker.run(state)


def repair_sql_node(state: dict):
    next_state = {**state, "retry_count": state.get("retry_count", 0) + 1}
    return _sql_worker.run(next_state)