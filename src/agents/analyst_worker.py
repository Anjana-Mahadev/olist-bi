# src/agents/analyst_worker.py

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import get_settings

settings = get_settings()


class AnalystWorker:
    def __init__(self):
        # Groq LLM for business analysis
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3,
        )

    def _build_safe_data_summary(self, db_result: dict) -> str:
        """
        Summarizes SQL results safely to prevent token overflow.
        """

        columns = db_result.get("columns", [])
        rows = db_result.get("rows", [])

        total_rows = len(rows)

        if total_rows == 0:
            return "Query returned 0 rows."

        # 🔥 LIMIT how many rows go to LLM
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

        # Handle DB error
        if "error" in db_result:
            return {
                **state,
                "analysis": f"Database Error: {db_result['error']}"
            }

        # Build safe summary
        safe_data_summary = self._build_safe_data_summary(db_result)

        prompt = f"""
You are a senior data analyst.

STRICT RULES:
- Only use values explicitly shown in the SQL result.
- Do NOT assume unseen data.
- Do NOT invent metrics.
- If rows are truncated, analyze only visible rows.
- Keep insights precise and data-driven.
- Avoid generic business advice.

User Question:
{state.get('question')}

SQL Query Used:
{state.get('sql_query')}

SQL Result Summary:
{safe_data_summary}

Provide:

1. Key Findings (bullet points)
2. Data-Backed Insights
3. Targeted Recommendations (ONLY if justified by data)
"""

        print("PROMPT LENGTH:", len(prompt))

        # 🔥 Emergency guard (extra safety)
        MAX_PROMPT_CHARS = 15000
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS]

        response = self.llm.invoke(
            [HumanMessage(content=prompt)]
        )

        return {
            **state,
            "analysis": response.content
        }