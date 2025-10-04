# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool

    class Config:
        orm_mode = True

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class OTPVerify(BaseModel):
    email: EmailStr
    code: str