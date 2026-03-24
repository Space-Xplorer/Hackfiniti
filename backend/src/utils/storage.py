import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2] / "data"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(application_id: str | int, name: str, payload: Any, metadata: dict[str, Any] | None = None) -> None:
    app_dir = BASE_DIR / str(application_id)
    app_dir.mkdir(parents=True, exist_ok=True)
    content = {"payload": payload, "metadata": metadata or {}}
    (app_dir / f"{name}.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def save_ocr_data(application_id: str | int, payload: Any, ocr_documents: list[dict[str, Any]] | None = None, metadata: dict[str, Any] | None = None) -> None:
    _write_json(application_id, "ocr_data", {"ocr_extracted_data": payload, "ocr_documents": ocr_documents or []}, metadata)


def save_validation_report(application_id: str | int, payload: Any, metadata: dict[str, Any] | None = None) -> None:
    _write_json(application_id, "validation_report", payload, metadata)


def save_derived_features(application_id: str | int, payload: Any, metadata: dict[str, Any] | None = None) -> None:
    _write_json(application_id, "derived_features", payload, metadata)


def save_model_output(application_id: str | int, payload: Any, metadata: dict[str, Any] | None = None) -> None:
    _write_json(application_id, "model_output", payload, metadata)
