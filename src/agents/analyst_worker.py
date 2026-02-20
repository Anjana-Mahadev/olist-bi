# src/agents/analyst_worker.py
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from src.config import get_settings

settings = get_settings()

class AnalystWorker:
    def __init__(self):
        # LLM for business analysis
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3
        )

    def run(self, state: dict):
        if "error" in state["db_result"]:
            return {
                **state,
                "analysis": f"Database Error: {state['db_result']['error']}"
            }

        prompt = f"""
        You are a senior business analyst.

        User Question:
        {state['question']}

        SQL Query:
        {state['sql_query']}

        Columns:
        {state['db_result']['columns']}

        Sample Rows (first 10):
        {state['db_result']['rows'][:10]}

        Provide:
        - Clear explanation
        - Key insights
        - Business recommendations
        Give numeric results clearly if possible.
        """

        response = self.llm.invoke([HumanMessage(content=prompt)])

        return {
            **state,
            "analysis": response.content
        }