import jwt
import os
from dotenv import load_dotenv

from datetime import datetime, timedelta,timezone
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, Base, get_db
from models.user import User
from models.shop import Shop
from models.role import Role
from models.product import *
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
        firstname=user.firstname,
        lastname=user.lastname,
        role_id=3, # Khách hàng,
        status='1'
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
                    "username": new_customer.username,
                    "email":new_customer.email,
                    "phone":new_customer.phone,
                    "firstname":new_customer.firstname,
                    "lastname":new_customer.lastname
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
        firstname=supplier.firstname,
        lastname=supplier.lastname,
        role_id=2, # Chủ shop,
        status='0'
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
                    "username": new_user.username,
                    "email":new_user.email,
                    "phone":new_user.phone,
                    "firstname":new_user.firstname,
                    "lastname":new_user.lastname
                    },SECRET_KEY
                )
            )
    )

@app.post("/signin/")
def signin(signin_data: SignIn, db: Session = Depends(get_db)):
    customer = db.query(User).filter(User.username == signin_data.username).first()
    if customer and verify_password(signin_data.password, customer.password_hash):
        if customer.status == '0':
            return ResponseAPI(
                status=-1,
                message="Tài khoản đã bị khoá",
                data=None
            )
        else:
            return ResponseAPI(
                status=1,
                message="Đăng nhập thành công",
                data=
                Token(
                token=generate_jwt_token(
                    {
                    "role_id": customer.role_id,
                    "username": customer.username,
                    "email":customer.email,
                    "phone":customer.phone,
                    "firstname":customer.firstname,
                    "lastname":customer.lastname
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

@app.post("/toggle-account-status/{username}/")  
def toggle_account_status(username: str, db: Session = Depends(get_db)):
    # Tìm account theo username
    account = db.query(User).filter(User.username == username).first()
    
    if account is None:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy account",
            data=None
        )
    
    # Kiểm tra trạng thái account, nếu status là False thì đặt là True
    # Nếu không, thì toggle ngược lại
    account.status = not account.status

    # Lưu thay đổi vào database
    db.commit()
    db.refresh(account)

    return ResponseAPI(
        status=1,
        message="Thay đổi trạng thái account thành công",
        data=None
    )

# tạo category
@app.post("/categories/{categoryname}/",response_model= CategoryBase)
def create_category(categoryname: str, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.category_name == categoryname).first()
    if db_category:
        return ResponseAPI(
            status=-1,
            message="Category đã tồn tại",
            data=None
        )
    # tạo category
    new_category = Category(category_name=categoryname)
    # print(new_category)
    # db.add(new_category)
    # db.commit()
    # db.refresh(new_category)
    return ResponseAPI(
        status=1,
        message="Thêm category thành công",
        data=CategoryBase(category_name=new_category.category_name)
    )

# tạo item liên kết với category
@app.post("/items/")
def create_item(item: ItemBase, db: Session = Depends(get_db)):
    new_item = Item(
        shop_id = item.shop_id,
        name=item.name,
        category_id=item.category_id,
        price=item.price,
        description=item.description,
        image_url=item.image_url,
    )
    # print(new_item)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return ResponseAPI(
        status=1,
        message="Thêm item thành công",
        data=
        ItemBase(
            shop_id = new_item.shop_id,
            name=new_item.name,
            category_id=new_item.category_id,
            price=new_item.price,
            description=new_item.description,
            image_url=new_item.image_url
        )
    )

@app.get("/items/{itemid}/")
def get_infor_item(itemid: int, db: Session = Depends(get_db)):
    itemid = db.query(Item).filter(Item.item_id == itemid).first()
    if itemid:
        item_info = Item(
            item_id = itemid.item_id,
            shop_id = itemid.shop_id,
            name=itemid.name,
            category_id=itemid.category_id,
            price=itemid.price,
            description=itemid.description,
            image_url=itemid.image_url
        )
        category_id = db.query(Category).filter(Category.category_id == itemid.category_id).first()
        item_detail_info = ItemDetail(
            item_id=item_info.item_id,
            shop_id=item_info.shop_id,
            name=item_info.name,
            category_id=item_info.category_id,
            category_name=category_id.category_name,
            price=item_info.price,
            description=item_info.description,
            image_url=item_info.image_url
        )
        return ResponseAPI(
            status=1,
            message="Lấy item thành công",
            data= item_detail_info
        )
    else:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy item",
            data=None
        )

@app.get("/items/", response_model=List[ItemBase])
def get_all_item(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(Item).join(Category).offset(skip).limit(limit).all()
    items_response = [
        ItemDetail(
            item_id=item.item_id,
            shop_id=item.shop_id,
            name=item.name,
            category_id=item.category_id,
            category_name=item.category.category_name,
            price=item.price,
            description=item.description,
            image_url=item.image_url,
        )
        for item in items
    ]

    return items_response