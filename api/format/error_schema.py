from pydantic import BaseModel
class ErrorSchema(BaseModel):
    status: int
    message: str

