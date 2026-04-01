from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import get_settings
from src.agents.llm_utils import safe_invoke


class AnalystWorker:
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

    def _build_safe_data_summary(self, db_result: dict) -> str:
        """
        Summarizes SQL results safely to prevent token overflow.
        """

        columns = db_result.get("columns", [])
        rows = db_result.get("rows", [])

        total_rows = len(rows)

        if total_rows == 0:
            return "Query returned 0 rows."

        MAX_ROWS_FOR_LLM = 20
        limited_rows = rows[:MAX_ROWS_FOR_LLM]

        summary = f"""
Total Rows Returned: {total_rows}

Columns:
{columns}

Showing First {len(limited_rows)} Rows:
{limited_rows}
"""

        return summary.strip()

    def run(self, state: dict):
        db_result = state.get("db_result", {})

        if "error" in db_result:
            return {
                **state,
                "analysis": f"Database error: {db_result['error']}",
            }

        safe_data_summary = self._build_safe_data_summary(db_result)
        prompt = f"""
You are a senior data analyst. Analyze the SQL query results and provide a clear, concise answer.

RULES:
- Only use values explicitly shown in the SQL result
- Do NOT assume unseen data
- Do NOT invent metrics
- Be precise and data-driven
- Avoid generic business advice
- Use clean prose or numbered points only
- Do NOT use markdown bullets or asterisk formatting
- Respond with plain text only (no JSON or schema)

User Question:
{state.get('question')}

SQL Query:
{state.get('sql_query')}

Data Results:
{safe_data_summary}

Provide your analysis below:
"""
        MAX_PROMPT_CHARS = 15000
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS]

        response = safe_invoke(self._get_llm(), [HumanMessage(content=prompt)], timeout_seconds=35)

        return {
            **state,
            "analysis": response.content.strip(),
        }


_analyst_worker = AnalystWorker()


def analyst_node(state: dict):
    return _analyst_worker.run(state)
