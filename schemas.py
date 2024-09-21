from pydantic import BaseModel, EmailStr
from typing import Any


class ResponseAPI(BaseModel):
    status: int
    message: str
    data: Any
    class Config:
        arbitrary_types_allowed = True


class UserSignUp(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    address: str
    role_id: int

class ShopSignUp(BaseModel):
    shop_name: str
    address: str
    phone: str
    description: str
    password: str

class SignIn(BaseModel):
    username: str
    password: str

class SignInReturn(BaseModel):
    role_id: int
    username: str
