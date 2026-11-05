from pydantic import BaseModel

class TestModel(BaseModel):
    id: int
    name: str
    is_active: bool = True
