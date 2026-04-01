import re


def _clean_answer_text(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)

    # Remove markdown emphasis markers while preserving inner text.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)\*(.*?)\*(?!\w)", r"\1", text)

    # Remove leading asterisk bullets from lines.
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("* "):
            indent = line[: len(line) - len(stripped)]
            cleaned_lines.append(f"{indent}{stripped[2:]}")
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def answer_composer_node(state: dict):
    intent = state.get("intent", "general")
    analysis = state.get("analysis", "")
    validation_errors = state.get("validation_errors", [])
    execution_error = state.get("execution_error", "")
    sql_query = state.get("sql_query", "")

    if intent != "data":
        final_answer = state.get("final_answer") or analysis
        response_type = state.get("response_type", intent)
    elif analysis:
        final_answer = analysis
        response_type = "data"
    elif validation_errors:
        final_answer = "I could not generate a safe SQL query for that request. Please rephrase it with the metric and dimension you want to analyze."
        response_type = "error"
    elif execution_error:
        final_answer = f"I could not execute a reliable SQL query for that request. Database error: {execution_error}"
        response_type = "error"
    elif sql_query:
        final_answer = "The workflow produced SQL but did not generate an analysis."
        response_type = "error"
    else:
        final_answer = "I could not complete the request. Please try a more specific Olist question."
        response_type = "error"

    cleaned_final_answer = _clean_answer_text(final_answer)
    cleaned_analysis = _clean_answer_text(analysis or cleaned_final_answer)

    return {
        **state,
        "analysis": cleaned_analysis,
        "final_answer": cleaned_final_answer,
        "response_type": response_type,
        "is_complete": True,
    }