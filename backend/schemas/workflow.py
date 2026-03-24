from pydantic import BaseModel


class WorkflowSubmitRequest(BaseModel):
    application_id: int


class WorkflowStatusResponse(BaseModel):
    application_id: int
    status: str
