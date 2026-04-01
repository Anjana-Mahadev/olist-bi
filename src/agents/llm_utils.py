from concurrent.futures import ThreadPoolExecutor, TimeoutError


def safe_invoke(llm, messages, timeout_seconds: int = 35):
    """Invoke an LLM call with a hard timeout to avoid stuck requests."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(llm.invoke, messages)
        try:
            return future.result(timeout=timeout_seconds)
        except TimeoutError as exc:
            raise RuntimeError(
                f"LLM request timed out after {timeout_seconds}s. Please try again."
            ) from exc
