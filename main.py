import jwt
import os
from dotenv import load_dotenv

from datetime import datetime, timedelta,timezone
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, Base, get_db
from models.user import User
from models.shop import Shop
from models.role import Role
from schemas import *
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

SECURITY_ALGORITHM = os.getenv('SECURITY_ALGORITHM')
SECRET_KEY = os.getenv('SECRET_KEY')


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tạo bảng trong database
Base.metadata.create_all(bind=engine)

# Bcrypt để mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_jwt_token(payload, secret_key, expiration_minutes=60):
    """
    Generate a JWT token with the provided payload, secret key, and expiration time.

    Args:
    - payload (dict): The data to include in the token's payload.
    - secret_key (str): The secret key used to sign the token.
    - expiration_minutes (int, optional): The token's expiration time in minutes. Default is 60 minutes.

    Returns:
    - str: The encoded JWT token.
    """
    # Set token expiration time
    expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    # Add expiration to the payload
    payload['exp'] = expiration

    # Generate the JWT token
    token = jwt.encode(payload, secret_key, SECURITY_ALGORITHM)
    
    return token

@app.post("/signup/customer/")
def signup_customer(user: UserSignUp, db: Session = Depends(get_db)):
    db_customer = db.query(User).filter(User.email == user.email).first()
    if db_customer:
        return ResponseAPI(
                status=-1,
                message="Đăng ký không thành công do tài khoản đã tồn tại trong hệ thống",
                data=None
            )
    # Kiem tra username trong database
    db_customer = db.query(User).filter(User.username == user.username).first()
    if db_customer:
        return ResponseAPI(
                status=-1,
                message="Đăng ký không thành công do tài khoản đã tồn tại trong hệ thống",
                data=None
        )
    hashed_password = get_password_hash(user.password)
    new_customer = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        address=user.address,
        role_id=3 # Khách hàng,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return ResponseAPI(
            status=1,
            message="Đăng ký thành công",
            data=
            Token(
                token=generate_jwt_token(
                    {
                    "role_id": new_customer.role_id,
                    "username": new_customer.username
                    },SECRET_KEY
                )
            )
        )
    

@app.post("/signup/supplier/")
def signup_supplier(supplier: ShopSignUp, db: Session = Depends(get_db)):

    db_customer = db.query(User).filter(User.email == supplier.email).first()
    if db_customer:
        return ResponseAPI(
                status=-1,
                message="Đăng ký không thành công do tài khoản đã tồn tại trong hệ thống",
                data=None
            )
    
    # Kiem tra username trong database
    db_customer = db.query(User).filter(User.username == supplier.username).first()
    if db_customer:
        return ResponseAPI(
                status=-1,
                message="Đăng ký không thành công do tài khoản đã tồn tại trong hệ thống",
                data=None
        )

    # tạo tài khoản
    hashed_password = get_password_hash(supplier.password)
    new_user = User(
        username=supplier.username,
        email=supplier.email,
        phone=supplier.phone,
        password_hash=hashed_password,
        address=supplier.address,
        role_id=2 # Chủ shop,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # check is the shop_phone is unique
    db_shop = db.query(Shop).filter(Shop.phone == supplier.shop_phone).first()
    if db_shop:
        return ResponseAPI(
            status=-1,
            message="Đăng ký shop thất bại do SĐT đã có người đăng ký trên hệ thống",
            data=None
        )

    # đăng ký shop
    new_shop = Shop(
        shop_name=supplier.shop_name,
        address=supplier.shop_address,
        phone=supplier.shop_phone,
        description=supplier.shop_description,
        owner_id=new_user.user_id
    )
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)

    return ResponseAPI(
        status=1,
        message="Đăng ký shop thành công",
        data=
        Token(
                token=generate_jwt_token(
                    {
                    "role_id": new_user.role_id,
                    "username": new_user.username
                    },SECRET_KEY
                )
            )
    )

@app.post("/signin/")
def signin(signin_data: SignIn, db: Session = Depends(get_db)):
    customer = db.query(User).filter(User.username == signin_data.username).first()
    if customer and verify_password(signin_data.password, customer.password_hash):
        return ResponseAPI(
                status=1,
                message="Đăng nhập thành công",
                data=
                Token(
                token=generate_jwt_token(
                    {
                    "role_id": customer.role_id,
                    "username": customer.username
                    },SECRET_KEY
                )
            )
        )
    else:
        return ResponseAPI(
            status=-1,
            message="Đăng nhập không thành công",
            data=None
        )
                
