from typing import TypedDict


class ApplicationState(TypedDict, total=False):
    application_id: int
    status: str
    result: dict
