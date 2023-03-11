from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime


class ContactModel(BaseModel):
    first_name: str = Field(min_length=1, max_length=25)
    last_name: str = Field(min_length=1, max_length=40)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)
    phone: int = Field(gt=100, le=999999999)
    birthday: date


class UpdateContactRoleModel(BaseModel):
    roles: str = Field("user")


class ContactDb(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        orm_mode = True


class ResponseContact(BaseModel):
    contact: ContactDb
    detail: str = "User was created successfully"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class ForgotPasswordModel(BaseModel):
    email: str


class ResetPasswordModel(BaseModel):
    email: EmailStr
    reset_password_token: str
    password: str
    confirm_password: str
