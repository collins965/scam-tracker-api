from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    reason: str
    recaptcha_token: str = Field(..., alias="recaptchaToken")

    class Config:
        allow_population_by_field_name = True

class UserLogin(BaseModel):
    email: str
    password: str
