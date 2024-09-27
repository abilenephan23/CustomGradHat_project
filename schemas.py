from pydantic import BaseModel, EmailStr
from typing import Any, Optional


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
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True

class ItemBase(BaseModel):
    name: str
    category_id: int
    price: int
    description: str
    image_url: str
    available_customization: bool

class ItemCreate(ItemBase):
    pass        

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True

