from pydantic import BaseModel, Field


class ProfileOut(BaseModel):
    name: str
    username: str
    phone: str
    bank: str
    requisites: str
    initials: str
    helped: int
    cards: int


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    bank: str = Field(min_length=2, max_length=64)
    requisites: str = Field(min_length=5, max_length=64)
