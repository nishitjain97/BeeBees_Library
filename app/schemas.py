from pydantic import BaseModel, Field
from typing import List

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author_first: str = Field(..., min_length=1, max_length=255)
    author_last: str = Field(..., min_length=1, max_length=255)
    year: str = Field(..., min_length=1, max_length=10)
    isbn: str = Field(..., min_length=1, max_length=32)

class BookCreate(BookBase):
    pass

class BookRead(BookBase):
    id: int
    class Config:
        from_attributes = True

class BookSearchResponse(BaseModel):
    items: List[BookRead]
    total: int
    page: int
    page_size: int