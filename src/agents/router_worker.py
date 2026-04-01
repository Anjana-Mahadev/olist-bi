import re

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from src.config import get_settings
from src.agents.llm_utils import safe_invoke


GREETING_PATTERNS = [
    r"\bhi\b",
    r"\bhey\b",
    r"\bhello\b",
    r"\bgreetings\b",
    r"\bgood morning\b",
    r"\bgood afternoon\b",
    r"\bgood evening\b",
]
GRATITUDE_PATTERNS = [r"\bthank you\b", r"\bthanks\b", r"\bappreciate\b"]
DATA_KEYWORDS = [
    "order",
    "orders",
    "product",
    "products",
    "customer",
    "customers",
    "seller",
    "sellers",
    "sales",
    "revenue",
    "review",
    "reviews",
    "rating",
    "payment",
    "payments",
    "delivery",
    "shipping",
    "freight",
    "city",
    "state",
    "category",
]
EXCLUDE_PATTERNS = [
    r"\bhow do i\b",
    r"\bhow can i\b",
    r"\bexplain\b",
    r"\btell me about\b",
    r"\bwhat is .{0,30}(python|javascript|java|machine learning|ai|algorithm)\b",
]


class ResponseWorker:
    def __init__(self):
        self.llm = None

    def _get_llm(self):
        if self.llm is None:
            settings = get_settings()
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0.2,
            )
        return self.llm

    def is_greeting(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(pattern, lowered) for pattern in GREETING_PATTERNS)

    def is_gratitude(self, text: str) -> bool:
        lowered = text.lower()
        return any(re.search(pattern, lowered) for pattern in GRATITUDE_PATTERNS)

    def is_data_question(self, text: str) -> bool:
        lowered = text.lower()
        if any(re.search(pattern, lowered) for pattern in EXCLUDE_PATTERNS):
            return False
        return any(keyword in lowered for keyword in DATA_KEYWORDS)

    def classify(self, question: str) -> str:
        stripped = question.strip()
        if not stripped:
            return "unsupported"
        if self.is_greeting(stripped):
            return "greeting"
        if self.is_gratitude(stripped):
            return "gratitude"
        if len(stripped.split()) < 2:
            return "unsupported"
        if self.is_data_question(stripped):
            return "data"
        return "general"

    def respond(self, state: dict):
        intent = state.get("intent", "general")
        question = state.get("question", "")

        if intent == "greeting":
            message = "Hi there. Ask me about Olist orders, products, customers, payments, or sales trends."
        elif intent == "gratitude":
            message = "You're welcome. Ask another Olist question whenever you're ready."
        elif intent == "unsupported":
            message = "Please ask a more specific question about the Olist dataset so I can route it correctly."
        else:
            prompt = f"""
You are the Olist BI assistant. The user asked a general question outside the Olist analytics workflow.

User question: {question}

Reply in 1-2 concise sentences. If appropriate, redirect the user toward Olist dataset questions.
""".strip()
            response = safe_invoke(self._get_llm(), [HumanMessage(content=prompt)], timeout_seconds=25)
            message = response.content.strip()

        return {
            **state,
            "analysis": message,
            "final_answer": message,
            "response_type": intent,
            "confidence": 1.0 if intent in {"greeting", "gratitude", "unsupported"} else 0.65,
            "is_complete": True,
        }


_response_worker = ResponseWorker()


def router_node(state: dict):
    intent = _response_worker.classify(state.get("question", ""))
    return {
        **state,
        "intent": intent,
        "response_type": intent,
    }


def responder_node(state: dict):
    return _response_worker.respond(state)


def route_after_routing(state: dict):
    return "data" if state.get("intent") == "data" else "respond"