from pydantic import BaseModel

class Node(BaseModel):
    uri: str

class Literal(BaseModel):
    value: str

class Triple(BaseModel):
    subject: Node
    predicate: Node
    object: Node | Literal

class Graph():
    triples: list[Triple]