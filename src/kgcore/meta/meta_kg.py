from pydantic import BaseModel

class MetaGraph(BaseModel):
    name: str
    model: str