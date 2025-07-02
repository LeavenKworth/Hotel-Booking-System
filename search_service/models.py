from pydantic import BaseModel

class SearchQuery(BaseModel):
    destination: str
    check_in: str
    check_out: str
    guests: int