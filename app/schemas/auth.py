from pydantic import BaseModel, Field, model_validator

_COMMON_PASSWORDS = {
    "password", "password1", "password123", "12345678", "123456789", "1234567890",
    "11111111", "qwertyui", "qwerty123", "iloveyou", "admin123", "letmein1",
}


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    # Версия документов, которую пользователь принял на стартовом экране.
    consent_version: str | None = Field(default=None, max_length=16)

    @model_validator(mode="after")
    def _check_password(self) -> "RegisterIn":
        lowered = self.password.lower()
        if lowered in _COMMON_PASSWORDS or lowered == self.username.lower():
            raise ValueError("Слишком простой пароль")
        return self


class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class AdminLoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=256)
