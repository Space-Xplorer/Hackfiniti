import logging
from pathlib import Path


def configure_workflow_logger() -> logging.Logger:
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "workflow.log"

    logger = logging.getLogger("workflow")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    logger.handlers.clear()
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(file_handler)
    return logger
