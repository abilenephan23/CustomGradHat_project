from pydantic import BaseModel, EmailStr

class CustomerSignUp(BaseModel):
    username: str
    email: EmailStr
    phone: str
    password: str
    address: str

class SupplierSignUp(BaseModel):
    shop_name: str
    address: str
    phone: str
    description: str
    password: str

class SignIn(BaseModel):
    username: str
    password: str