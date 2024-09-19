from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, Base, get_db
from models.user import Customer, Supplier
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
def signup_customer(customer: CustomerSignUp, db: Session = Depends(get_db)):
    db_customer = db.query(Customer).filter(Customer.email == customer.email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    hashed_password = get_password_hash(customer.password)
    new_customer = Customer(
        username=customer.username,
        email=customer.email,
        phone=customer.phone,
        password=hashed_password,
        address=customer.address
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return {"message": "Đăng ký thành công", "customer": new_customer}

@app.post("/signup/supplier/")
def signup_supplier(supplier: SupplierSignUp, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(supplier.password)
    new_supplier = Supplier(
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
    customer = db.query(Customer).filter(Customer.username == signin_data.username).first()
    supplier = db.query(Supplier).filter(Supplier.shop_name == signin_data.username).first()

    if customer and verify_password(signin_data.password, customer.password):
        return {"message": "Đăng nhập thành công", "user": "customer"}
    elif supplier and verify_password(signin_data.password, supplier.password):
        return {"message": "Đăng nhập thành công", "user": "supplier"}
    else:
        raise HTTPException(status_code=400, detail="Thông tin đăng nhập không hợp lệ")
