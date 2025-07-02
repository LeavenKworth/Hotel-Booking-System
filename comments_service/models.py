from pydantic import BaseModel

class Comment(BaseModel):
    _id: str | None = None
    ratings: dict
    comment: str