from pydantic import BaseModel, EmailStr
from typing import Any, Optional
from models.role import Role
from typing import List



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


class ShopDetail(BaseModel):
    shop_id: int
    phone: str
    shop_name: str
    phone: str
    address: str
    description: str
    status: str

    class Config:
        orm_mode = True


class CategoryBase(BaseModel):
    category_id: int
    category_name: str

# Define a schema for Color input
class ColorCreate(BaseModel):
    color_label: str

# Define a schema for Size input
class SizeCreate(BaseModel):
    size_label: str


class ColorDTO(BaseModel):
    color_id: int
    color_label: str


class SizeDTO(BaseModel):
    size_id: int
    size_label: str

class ItemBase(BaseModel):
    shop_id: int
    name: str
    category_id: int
    price: int
    description: str
    image_url: str
    quantity: int
    colors: List[ColorCreate]
    sizes: List[SizeCreate]
    status: str

    class Config:
        orm_mode = True


class ItemDetail(ItemBase):
    item_id: int
    category_name: str
    colors: List[ColorDTO]  # Use ColorDTO here
    sizes: List[SizeDTO]    # Use SizeDTO here
    status: str
    shop: ShopDetail
    

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
    address: str
    role: RoleResponse  # Use the RoleResponse model
    status: str
    shop: Optional[ShopDetail] = None  # Make the shop field optional

    class Config:
        orm_mode = True

class CustomizationCreate(BaseModel):
    item_id: int
    price_adjustment: int
    image_url: str
    description: str
    is_shop_owner_created: str

class CustomizationResponse(BaseModel):
    customization_id: int
    item_id: int
    price_adjustment: int
    image_url: str
    description: str
    is_shop_owner_created: str

    class Config:
        orm_mode = True

class OrderRespond(BaseModel):
    order_id: int
    customer_id: int
    quantity: int
    total_price: int
    order_at: str
    order_status: int
    payment_id: int
    response: str
    img_url: str
    variation_id: int
    customization_id: int

    class Config:
        orm_mode = True

class ItemOrderCreate(BaseModel):
    item_id: int
    item_quantity: int
    color_id: int
    size_id:int

class CustomizationCreate(BaseModel):
    customization_id: int

class PaymentOrderCreate(BaseModel):
    payment_id: int
    payment_status: int

class OrderCreate(BaseModel):
    customer_id: int
    total_price: int
    customer_address: str
    customer_name: str
    customer_phone: str
    items: Optional[List[ItemOrderCreate]] = None
    image_url: str 
    customizations: Optional[List[CustomizationCreate]] = None  # Make the customizations field optional 

class OrderCreateResponse(BaseModel):
    url: str
