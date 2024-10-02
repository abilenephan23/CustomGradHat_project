from pydantic import BaseModel, EmailStr
from typing import Any, Optional
from models.role import Role



class ResponseAPI(BaseModel):
    status: int
    message: str
    data: Any
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class UserSignUp(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    address: str
    firstname: str
    lastname: str

class ShopSignUp(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    address: str
    firstname: str
    lastname: str
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

class CategoryBase(BaseModel):
    category_id: int
    category_name: str


class ItemBase(BaseModel):
    shop_id: int
    name: str
    category_id: int
    price: int
    description: str
    image_url: str

class ItemDetail(ItemBase):
    item_id: int
    category_name: str

class RoleResponse(BaseModel):
    role_id: int
    role_name: str

    class Config:
        orm_mode = True

# Pydantic schema for User (to serialize the response)
class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    firstname: str
    lastname: str
    phone: str
    role: RoleResponse  # Use the RoleResponse model
    status: str

    class Config:
        orm_mode = True

