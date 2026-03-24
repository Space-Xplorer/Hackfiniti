import logging


logger = logging.getLogger("workflow")


def log_request(request_id: str, request_type: str) -> None:
    logger.info("request_id=%s request_type=%s", request_id, request_type)


def log_agent_execution(agent: str, request_id: str, status: str, duration_ms: float | None = None) -> None:
    if duration_ms is None:
        logger.info("agent=%s request_id=%s status=%s", agent, request_id, status)
    else:
        logger.info("agent=%s request_id=%s status=%s duration_ms=%.2f", agent, request_id, status, duration_ms)


def log_error(component: str, message: str, request_id: str | None = None) -> None:
    if request_id:
        logger.error("component=%s request_id=%s error=%s", component, request_id, message)
    else:
        logger.error("component=%s error=%s", component, message)
