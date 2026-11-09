from pydantic import BaseModel, Field, field_validator

from app.core.validators import normalize_phone, normalize_requisites


class ProfileOut(BaseModel):
    name: str
    username: str
    phone: str
    bank: str
    requisites: str
    initials: str
    helped: int
    cards: int
    legal_accepted: bool = True


class ConsentIn(BaseModel):
    version: str = Field(max_length=16)


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    bank: str = Field(min_length=2, max_length=64)
    requisites: str = Field(min_length=5, max_length=64)

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("requisites")
    @classmethod
    def _check_requisites(cls, value: str) -> str:
        return normalize_requisites(value)


class DeleteAccountIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)
