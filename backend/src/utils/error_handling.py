from functools import wraps


def safe_agent_wrapper(func):
    @wraps(func)
    def _wrapped(state):
        try:
            return func(state)
        except Exception as exc:
            state = state or {}
            state.setdefault("errors", []).append(f"{func.__name__}: {exc}")
            return state

    return _wrapped
