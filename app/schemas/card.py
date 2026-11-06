from pydantic import BaseModel, Field


class CardPublic(BaseModel):
    id: str
    amount: int
    purpose: str
    category: str
    author: str
    initials: str
    color: str


class CardCreate(BaseModel):
    amount: int = Field(gt=0, le=1_000_000)
    purpose: str = Field(min_length=10, max_length=160)
    category: str = Field(min_length=2, max_length=64)


class CardCreated(CardPublic):
    pass


class HelpOut(BaseModel):
    id: str
    author: str
    bank: str
    requisites: str
