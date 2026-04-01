COMPLEXITY_KEYWORDS = [
    "compare",
    "versus",
    "vs",
    "trend",
    "over time",
    "relationship",
    "correlation",
    "impact",
    "breakdown",
    "segment",
    "monthly",
    "quarterly",
    "yearly",
]


def planner_node(state: dict):
    question = state.get("question", "")
    lowered = question.lower()
    is_complex = any(keyword in lowered for keyword in COMPLEXITY_KEYWORDS) or lowered.count(" and ") > 0
    complexity = "complex" if is_complex else "simple"

    if is_complex:
        plan = [
            "Identify the relevant metrics and comparison dimensions.",
            "Generate a grounded SQL query using only the selected schema.",
            "Summarize findings and note any evidence limits.",
        ]
    else:
        plan = [
            "Generate a single SQL query that answers the question directly.",
            "Summarize the result in plain language.",
        ]

    return {
        **state,
        "complexity": complexity,
        "plan": plan,
        "confidence": 0.8 if is_complex else 0.9,
    }


def decomposer_node(state: dict):
    question = state.get("question", "")
    lowered = question.lower()
    split_tokens = [" and ", " versus ", " vs "]
    sub_questions = []

    for token in split_tokens:
        if token in lowered:
            sub_questions = [part.strip().rstrip("?") for part in question.split(token) if part.strip()]
            break

    if not sub_questions:
        sub_questions = [question.strip()]

    return {
        **state,
        "sub_questions": sub_questions,
    }


def route_after_planning(state: dict):
    return "decompose" if state.get("complexity") == "complex" else "sql"