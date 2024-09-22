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

class ShopSignUp(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    address: str
    shop_name: str
    shop_phone: str
    shop_address: str
    shop_description: str

class SignIn(BaseModel):
    username: str
    password: str

class SignInReturn(BaseModel):
    role_id: int
    username: str

class SignUpReturn(BaseModel):
    role_id: int
    username: str
class Token(BaseModel):
    token: str
