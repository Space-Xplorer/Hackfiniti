from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    product_type: str


class ApplicationRead(BaseModel):
    id: int
    user_id: int
    product_type: str
    status: str
