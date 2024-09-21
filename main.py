from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, Base, get_db
from models.user import User, Shop
from schemas import *

app = FastAPI()

# Tạo bảng trong database
Base.metadata.create_all(bind=engine)

# Bcrypt để mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@app.post("/signup/customer/")
def signup_customer(user: UserSignUp, db: Session = Depends(get_db)):
    db_customer = db.query(User).filter(User.email == user.email).first()
    if db_customer:
        return ResponseAPI(
                status=-1,
                message="Đăng ký không thành công",
                data=None
            )
    hashed_password = get_password_hash(user.password)
    new_customer = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        address=user.address,
        role_id=user.role_id,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return ResponseAPI(
            status=1,
            message="Đăng ký thành công",
            data= new_customer
        )
    

@app.post("/signup/supplier/")
def signup_supplier(supplier: ShopSignUp, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(supplier.password)
    new_supplier = Shop(
        shop_name=supplier.shop_name,
        address=supplier.address,
        phone=supplier.phone,
        description=supplier.description,
        password=hashed_password
    )
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return {"message": "Đăng ký thành công", "supplier": new_supplier}

@app.post("/signin/")
def signin(signin_data: SignIn, db: Session = Depends(get_db)):
    customer = db.query(User).filter(User.username == signin_data.username).first()
    supplier = db.query(Shop).filter(Shop.shop_name == signin_data.username).first()

    if customer and verify_password(signin_data.password, customer.password_hash):
        return ResponseAPI(
                status=1,
                message="Đăng nhập thành công",
                data=SignInReturn(
                    role_id=customer.role_id,
                    username=customer.username
                )
            )
    else:
        return ResponseAPI(
            status=-1,
            message="Đăng nhập không thành công",
            data=None
        )
                
