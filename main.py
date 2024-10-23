import jwt
import os
import time
from dotenv import load_dotenv

from datetime import datetime, timedelta,timezone
from fastapi import FastAPI, Depends, HTTPException, status,Query,Request
from typing import List
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import engine, Base, get_db
from models.user import User
from models.shop import Shop
from models.role import Role
from models.order import Order, OrderDetails
from models.product import *
from schemas import *
from fastapi.middleware.cors import CORSMiddleware
from crud import *
from payment import get_payment_url
from starlette.responses import RedirectResponse
from payos import PayOS, ItemData, PaymentData
from sqlalchemy import cast, String
from datetime import datetime, timedelta





load_dotenv()

SECURITY_ALGORITHM = os.getenv('SECURITY_ALGORITHM')
SECRET_KEY = os.getenv('SECRET_KEY')
SUCCESS_ORDER_URL = os.getenv('SUCCESS_ORDER_URL')
FAILURE_ORDER_URL = os.getenv('FAILURE_ORDER_URL')

PAYOS_CLIENT_ID = os.getenv('PAYOS_CLIENT_ID')
PAYOS_API_KEY = os.getenv('PAYOS_API_KEY')
PAYOS_CHECKSUM_KEY = os.getenv('PAYOS_CHECKSUM_KEY')
RETURN_URL=os.getenv('RETURN_URL')

payos = PayOS(PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY)



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
        owner_id=new_user.user_id,
        status='1'
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
                message="Tài khoản đã bị khóa",
                data=None
            )
        else:
            # If the user is a shop owner (role_id == 2), include shop ID in the token as a string
            if customer.role_id == 2:
                shop_id = str(customer.shops[0].shop_id) if customer.shops else None  # Get the first shop ID as a string
                return ResponseAPI(
                    status=1,
                    message="Đăng nhập thành công",
                    data=Token(
                        token=generate_jwt_token(
                            {
                                "user_id": customer.user_id,
                                "role_id": customer.role_id,
                                "username": customer.username,
                                "email": customer.email,
                                "phone": customer.phone,
                                "firstname": customer.firstname,
                                "lastname": customer.lastname,
                                "shop_id": shop_id  # Include shop ID as a string in the token
                            },
                            SECRET_KEY
                        )
                    )
                )
            else:
                return ResponseAPI(
                    status=1,
                    message="Đăng nhập thành công",
                    data=Token(
                        token=generate_jwt_token(
                            {
                                "user_id": customer.user_id,
                                "role_id": customer.role_id,
                                "username": customer.username,
                                "email": customer.email,
                                "phone": customer.phone,
                                "firstname": customer.firstname,
                                "lastname": customer.lastname,
                                "address": customer.address
                            },
                            SECRET_KEY
                        )
                    )
                )
    else:
        return ResponseAPI(
            status=-1,
            message="Đăng nhập không thành công do sai mật khẩu hoặc tài khoản",
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

@app.post("/items/", response_model=ResponseAPI)
def create_item(item: ItemBase, db: Session = Depends(get_db)):

    # Create and add the colors to the database and return the color IDs
    color_ids = []
    for color in item.colors:
        new_color = Color(color_label=color.color_label)
        db.add(new_color)
        db.commit()
        db.refresh(new_color)
        color_ids.append(new_color.color_id)

    # Create and add the sizes to the database and return the size IDs
    size_ids = []
    for size in item.sizes:
        new_size = Size(size_label=size.size_label)
        db.add(new_size)
        db.commit()
        db.refresh(new_size)
        size_ids.append(new_size.size_id)

    # Create the new item
    new_item = Item(
        shop_id=item.shop_id,
        name=item.name,
        category_id=item.category_id,
        price=item.price,
        description=item.description,
        image_url=item.image_url,
        quantity=item.quantity,
        status='1'
    )

    # Add the new item to the database
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    # Add the colors to the ItemColors table
    for color_id in color_ids:
        item_color = ItemColors(item_id=new_item.item_id, color_id=color_id)
        db.add(item_color)
    
    # Add the sizes to the ItemSizes table
    for size_id in size_ids:
        item_size = ItemSizes(item_id=new_item.item_id, size_id=size_id)
        db.add(item_size)
    
    # Commit the colors and sizes to the database
    db.commit()

    # Return a response
    return {
        "status": 1,
        "message": "Item created successfully",
        "data": {
            "item_id": new_item.item_id,
            "shop_id": new_item.shop_id,
            "name": new_item.name,
            "category_id": new_item.category_id,
            "price": new_item.price,
            "description": new_item.description,
            "image_url": new_item.image_url,
            "quantity": new_item.quantity,
            "colors": [color.color_label for color in item.colors],
            "sizes": [size.size_label for size in item.sizes]
        }
    }

@app.get("/items/", response_model=ResponseAPI)
def get_all_item(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),  # Limit for pagination
):
    skip = (page - 1) * limit

    # Query to get total number of items
    total_items = db.query(Item).count()
    
    # Query to get the paginated items
    items = db.query(Item).offset(skip).limit(limit).all()

    total_pages = (total_items + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

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
            quantity=item.quantity,
            # Create a dictionary for each color using ColorCreate
            colors=[ColorDTO(color_id=color.color_id, color_label=color.color_label) 
                    for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()],
            # Create a dictionary for each size using SizeCreate
            sizes=[SizeDTO(size_id=size.size_id, size_label=size.size_label) 
                   for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()],
            status=item.status,
            shop= ShopDetail(
                shop_id=item.shop_id,
                shop_name=item.shop.shop_name,
                address=item.shop.address,
                phone=item.shop.phone,
                description=item.shop.description,
                status=item.shop.status
            )           
        )
        for item in items
    ]

    return ResponseAPI(
        status=1,
        message="Lấy danh sách sản phẩm thành công!",
        data={
            "items": items_response,
            "pagination": {
                "total_records": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        }
    )


# API to get all users except "admin", with pagination
@app.get("/users", response_model=ResponseAPI)
def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),  # Limit for pagination
):
    # Calculate skip value based on 1-based page index
    skip = (page - 1) * limit

    # Query to get total number of users except the one with username 'admin'
    total_users = db.query(User).filter(User.username != "admin").count()
    
    # Query to get the paginated users
    users = db.query(User).filter(User.username != "admin").offset(skip).limit(limit).all()

    # Calculate pagination details
    total_pages = (total_users + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    # Convert SQLAlchemy User objects to dictionary or required fields for Pydantic validation
    user_responses = [
        UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            firstname=user.firstname,
            lastname=user.lastname,
            address=user.address,
            role=RoleResponse(  # Pass the Role object
                role_id=user.role.role_id,
                role_name=user.role.role_name,
            ),            
            status=user.status,
             # Handle the case when user does not have a shop (set shop to None)
            shop=ShopDetail(
                shop_id=user.shops[0].shop_id,
                shop_name=user.shops[0].shop_name,
                address=user.shops[0].address,
                phone=user.shops[0].phone,
                description=user.shops[0].description,
                status=user.shops[0].status
            ) if user.shops else None
        ) 
        for user in users
    ]

    # Return the response with paginated data and pagination metadata
    return ResponseAPI(
    status=1,
    message="Lấy danh sách người dùng thành công!",
    data={
        "users": user_responses,
        "pagination": {
            "total_records": total_users,
            "total_pages": total_pages,
            "current_page": page,
            "next_page": next_page,
            "prev_page": prev_page
        }
    }
)

@app.get("/shop-items/{shop_id}")
def get_shop_items(
    shop_id = int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),
):
    
    # Tìm shop
    shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    if not shop:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy shop",
            data=None
        )
    
    skip = (page - 1) * limit
    total_items = db.query(Item).count()
    items = db.query(Item).filter(Item.shop_id == shop_id).offset(skip).limit(limit).all()
    total_pages = (total_items + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None
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
            quantity=item.quantity,
            # Create a dictionary for each color using ColorCreate
            colors=[ColorDTO(color_id=color.color_id, color_label=color.color_label) 
                    for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()],
            # Create a dictionary for each size using SizeCreate
            sizes=[SizeDTO(size_id=size.size_id, size_label=size.size_label) 
                   for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()],
            status=item.status,
            shop=ShopDetail(
                shop_id=shop.shop_id,
                shop_name=shop.shop_name,
                address=shop.address,
                phone=shop.phone,
                description=shop.description,
                status=shop.status
            )       
        )
        for item in items
    ]
    return ResponseAPI(
        status=1,
        message="Lấy danh sách san pham cua shop thanh cong!",
        data = {
            "items": items_response,
            "pagination": {
                "total_records": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        })

# api customize
@app.post("/customizations")
def create_customization(customization: CustomizationCreate, db: Session = Depends(get_db)):
    return create_customizations(db, customization)

@app.get("/customizations/{customization_id}")
def read_customization(customization_id : int, db: Session = Depends(get_db)):
    return get_customization_by_id(db, customization_id)

@app.get("/customizations", response_model=ResponseAPI)
def read_custom_by_page(
    db: Session = Depends(get_db), 
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1)):
    # Calculate skip value based on 1-based page index
    skip = (page - 1) * limit

    # Query to get total number of customizations
    total_custom = db.query(Customization).count()
    
    # Query to get the paginated customizations
    customs = db.query(Customization).offset(skip).limit(limit).all()

    # Calculate pagination details
    total_pages = (total_custom + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    # Convert SQLAlchemy User objects to dictionary or required fields for Pydantic validation
    custom_responses = [
        CustomizationResponse(
            customization_id=custom.customization_id,
            item_id=custom.item_id,
            price_adjustment=custom.price_adjustment,
            image_url=custom.image_url,
            description=custom.description,
            is_shop_owner_created=custom.is_shop_owner_created
        ) 
        for custom in customs
    ]

    # Return the response with paginated data and pagination metadata
    return ResponseAPI(
    status=1,
    message="Lấy danh sách custom thành công!",
    data={
        "customizations": custom_responses,
        "pagination": {
            "total_records": total_custom,
            "total_pages": total_pages,
            "current_page": page,
            "next_page": next_page,
            "prev_page": prev_page
        }
    }
    )
@app.put("/customizations/{customization_id}")
def update_customization(customization_id: int, customization: CustomizationCreate, db: Session = Depends(get_db)):
    return update_customizations(db, customization_id, customization)

@app.delete("/customizations/{customization_id}")
def delete_customization(customization_id: int, db: Session = Depends(get_db)):
    return delete_customizations(db, customization_id)
# API get all categories
@app.get("/categories", response_model=ResponseAPI)
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    categories_response = [
        CategoryBase(
            category_id=category.category_id,
            category_name=category.category_name
        )
        for category in categories
    ]
    return ResponseAPI(
        status=1,
        message="Lấy danh sách category thanh cong!",
        data=categories_response
    )

# API Get item by id
@app.get("/items/{item_id}", response_model=ResponseAPI)
def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.item_id == item_id).first()
    if not item:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy item",
            data=None
        )
    return ResponseAPI(
        status=1,
        message="Lấy item thanh cong!",
        data=ItemDetail(
            item_id=item.item_id,
            shop_id=item.shop_id,
            name=item.name,
            category_id=item.category_id,
            category_name=item.category.category_name,
            price=item.price,
            description=item.description,
            image_url=item.image_url,
            quantity=item.quantity,
            # Create a dictionary for each color using ColorCreate
            colors=[ColorDTO(color_id=color.color_id, color_label=color.color_label) 
                    for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()],
            # Create a dictionary for each size using SizeCreate
            sizes=[SizeDTO(size_id=size.size_id, size_label=size.size_label) 
                   for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()],
            status=item.status,
            shop= ShopDetail(
                shop_id=item.shop_id,
                shop_name=item.shop.shop_name,
                address=item.shop.address,
                phone=item.shop.phone,
                description=item.shop.description,
                status=item.shop.status
            )           
        )
    )

# API create order
@app.post("/orders/", response_model=ResponseAPI)
def create_order(order: OrderCreate, request: Request, db: Session = Depends(get_db)):

    try:
        # Step 1: Begin the transaction
        with db.begin():
            # Step 2: Create the order with status and response as null
            new_order = Order(
                customer_id=order.customer_id,
                total_price=order.total_price,
                customer_address=order.customer_address,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                image_url=order.image_url,
                order_status=None,  # Null status initially
                response=None,  # No response yet
                payment_status=None,
                shipping_status=None
            )
            db.add(new_order)
            db.flush()  # Ensure the order_id is available for OrderDetails

            # Step 3: Map the items, colors, sizes, customizations to order_details
            if order.items:
                for item in order.items:
                    # Fetch the item from the database
                    db_item = db.query(Item).filter(Item.item_id == item.item_id).first()
                    if not db_item:
                        db.rollback()
                        return ResponseAPI(
                            status=-1,
                            message=f"Item with ID {item.item_id} not found",
                            data=None
                        )
                    
                    # Check if the item is available in sufficient quantity
                    if db_item.quantity < item.item_quantity:
                        db.rollback()
                        return ResponseAPI(
                            status=-1,
                            message=f"Item with ID {item.item_id} is out of stock",
                            data=None
                        )
                    
                    # Deduct the quantity
                    db_item.quantity -= item.item_quantity

                    # Add to OrderDetails
                    order_detail = OrderDetails(
                        order_id=new_order.order_id,
                        item_id=item.item_id,
                        item_quantity=item.item_quantity,
                        color_id=item.color_id,  # Assuming you may add logic to select color and size
                        size_id=item.size_id
                    )
                    db.add(order_detail)

            # Step 4: Handle customizations (if any)
            if order.customizations:
                for customization in order.customizations:
                    #  create customizations first
                    new_customization = Customization(
                        price_adjustment = customization.price_adjustment,
                        image_url = customization.image_url,
                        description = customization.description,
                        is_shop_owner_created = '0'
                    )
                    db.add(new_customization)
                    db.flush()  # Ensure the customization_id is available for OrderDetails
                    # Create order details with customizations
                    order_detail = OrderDetails(
                        order_id=new_order.order_id,
                        customization_id=new_customization.customization_id,
                        item_id=None  # No item in this case
                    )
                    db.add(order_detail)

            # Step 5: Commit the transaction
            db.commit()


        itemsPayos = []
        # create payment data url with pay os
        if order.items:
            for item in order.items:
                item = ItemData(name=item.item_name, price=item.item_price, quantity=item.item_quantity)
                itemsPayos.append(item)
            
        if order.customizations:
            for customize in order.customizations:
                custom = ItemData(name=customize.description,price=customize.price_adjustment,quantity=1)
                itemsPayos.append(custom)

        paymentData = PaymentData(
            orderCode=new_order.order_id,
            amount=int(new_order.total_price),
            description='Thanh toan tai Spotlight',
            items=itemsPayos,
            cancelUrl=RETURN_URL,
            returnUrl=RETURN_URL

        )

        payment_link_response = payos.createPaymentLink(paymentData)



        # Step 6: Create a payment link for VNpay and return the response
        return ResponseAPI(
            status=1,
            message="Order created successfully",
            data=OrderCreateResponse(
                url=payment_link_response.checkoutUrl
            )
        )

    except HTTPException as e:
        # Rollback the transaction in case of HTTP exceptions
        db.rollback()
        return ResponseAPI(status=-1, message=str(e.detail), data=None)

    except Exception as e:
        # Rollback the transaction in case of any other exceptions
        db.rollback()
        return ResponseAPI(status=-1, message="Failed to create order: " + str(e) + "", data=None)


# API order callback
@app.get("/orders/callback")
def order_callback(vnp_Data:str = None,vnp_ResponseCode:str = None,db: Session = Depends(get_db)):
    if vnp_ResponseCode == "00":
        # update order status base on vnp_Data which is the order id
        order = db.query(Order).filter(Order.order_id == vnp_Data).first()
        if not order:
            return ResponseAPI(
            status=-1,
            message="Đơn hàng không tồn tại trong hệ thống",
            data=None
        )
        order.payment_status = '1'
        db.commit()
        db.refresh(order)
        return RedirectResponse(url=SUCCESS_ORDER_URL)
    else:
        # update order status base on vnp_Data which is the order id
        order = db.query(Order).filter(Order.order_id == vnp_Data).first()
        if not order:
            return ResponseAPI(
            status=-1,
            message="Đơn hàng không tồn tại trong hệ thống",
            data=None
        )
        order.order_status = '0'
        order.response = "Đơn hàng đã bị hủy"
        order.payment_status = '0'
        order.shipping_status = '0'
        # return the quantity back to the item
        db_item = db.query(Item).filter(Item.item_id == order.item_id).first()
        if not db_item:
            return ResponseAPI(
            status=-1,
            message="Sản phẩm không tồn tại trong hệ thống",
            data=None
        )
        db_item.quantity += order.item_quantity
        db.commit()
        db.refresh(order)
        return RedirectResponse(url=FAILURE_ORDER_URL)

# cần optimize lại kết quả trả về
@app.get("/items/name/{item_name}")
def get_all_item_by_name(
    item_name: str,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),  # Limit for pagination
):
    item_name_default = item_name.lower()
    try:
        skip = (page - 1) * limit
        items = db.query(Item).filter(
        Item.name.ilike(f"%{item_name_default}%")
            ).offset(skip).limit(limit).all()
        
    except Exception as e:
        raise ResponseAPI(
            status=-1,
            message="Không tìm thấy sản phẩm",
            data=None
        )


    total_items = db.query(Item).filter(
        Item.name.ilike(f"%{item_name_default}%")
    ).count()
    
    total_pages = (total_items + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

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
            quantity=item.quantity,
            # Create a dictionary for each color using ColorCreate
            colors=[ColorDTO(color_id=color.color_id, color_label=color.color_label) 
                    for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()],
            # Create a dictionary for each size using SizeCreate
            sizes=[SizeDTO(size_id=size.size_id, size_label=size.size_label) 
                for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()],
            status=item.status,
            shop= ShopDetail(
                shop_id=item.shop_id,
                shop_name=item.shop.shop_name,
                address=item.shop.address,
                phone=item.shop.phone,
                description=item.shop.description,
                status=item.shop.status
            )           
        )
        for item in items
]
    

    return ResponseAPI(
        status=1,
        message="Lấy danh sách sản phẩm thành công!",
        data={
            "items": items_response,
            "pagination": {
                "total_records": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        }
    )
    

@app.get("/orders/callback-payos")
def order_callback_payos(orderCode:str = None,code:str = None,id:str = None,cancel: str = None,status: str = None,db: Session = Depends(get_db)):
   if code == "00":
        if status == "PAID":
            # update order status base on vnp_Data which is the order id
            order = db.query(Order).filter(Order.order_id == orderCode).first()
            if not order:
                return ResponseAPI(
                status=-1,
                message="Đơn hàng không tồn tại trong hệ thống",
                data=None
            )
            order.payment_status = '1'
            db.commit()
            db.refresh(order)
            return RedirectResponse(url=SUCCESS_ORDER_URL)
        elif status == "CANCELLED":
             # update order status base on vnp_Data which is the order id
            order = db.query(Order).filter(Order.order_id == orderCode).first()
            if not order:
                return ResponseAPI(
                status=-1,
                message="Đơn hàng không tồn tại trong hệ thống",
                data=None
            )
            order.order_status = '0'
            order.response = "Đơn hàng đã bị hủy"
            order.payment_status = '0'
            # Return the quantity back to the item
            for item in order.details:
                db_item = db.query(Item).filter(Item.item_id == item.item_id).first()
                if db_item:  # Check if db_item exists
                    db_item.quantity += item.item_quantity
                else:
                    # Handle case if the item does not exist
                    # Optionally log this for debugging
                    print(f"Item with ID {item.item_id} not found when trying to restock.")


            
            db.commit()
            db.refresh(order)
            return RedirectResponse(url=FAILURE_ORDER_URL)
   else:
    return RedirectResponse(url=FAILURE_ORDER_URL)

@app.get("/orders/{shop_id}", response_model=ResponseAPI)
def get_users_order(
    shop_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),
):
    skip = (page - 1) * limit
    total_orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .filter(Item.shop_id == shop_id)
        .count()
    )
    total_pages = (total_orders + limit - 1) // limit  # Round up
    orders = get_orders_by_shop(db, shop_id,skip, limit)
    if not orders:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng",
            data=None
        )
    
    order_response = [
        {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "total_price": float(order.total_price),
            "order_at": order.order_at,
            "order_status": order.order_status,
            "response": order.response,
            "customer_address": order.customer_address,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "image_url": order.image_url,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
            "items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "category": {
                        "category_id": item.category.category_id,
                        "category_name": item.category.category_name
                    },
                    "price": float(item.price),
                    "description": item.description,
                    "image_url": item.image_url,
                    "status": item.status,
                    "item_quantity": details.item_quantity,
                    "color": {
                        "color_id": color.color_id,
                        "color_label": color.color_label
                    },
                    "size": {
                        "size_id": size.size_id,
                        "size_label": size.size_label
                    },
                    "shop": {
                        "shop_id": item.shop.shop_id,
                        "shop_name": item.shop.shop_name,
                        "address": item.shop.address,
                        "phone": item.shop.phone,
                        "description": item.shop.description,
                        "status": item.shop.status
                    }
                }
                for details in order.details
                for item in db.query(Item).filter(Item.item_id == details.item_id).all()
                for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()
                for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()
            ],
            "customizations": [
                {
                    "customization_id": customization.customization_id,
                    "item_id": customization.item_id,
                    "price_adjustment": customization.price_adjustment,
                    "description": customization.description,
                    "image_url": customization.image_url,
                    "is_shop_owner_created": customization.is_shop_owner_created
                }
                for details in order.details
                for customization in db.query(Customization)
                    .filter(Customization.customization_id == details.customization_id).all()
            ]
        }
        for order in orders
    ]
    # Tính trang trước và trang kế
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None
    return ResponseAPI(
        status=1,
        message="Lấy đơn hàng thành công",
        data={
            "orders": order_response,
            "pagination": {
                "total_records": total_orders,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        }
    )
       
@app.get("/user/orders/{user_id}", response_model=ResponseAPI)
def get_user_orders(
    user_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    skip = (page - 1) * limit
    # Lấy tổng số đơn hàng của người dùng
    total_orders = db.query(Order).filter(Order.customer_id == user_id).count()
     # Tính tổng số trang
    total_pages = (total_orders + limit - 1) // limit  # Làm tròn lên
    # Lấy danh sách đơn hàng của người dùng
    orders = get_orders_by_user(db, user_id, skip, limit)
    
    if not orders:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng của người dùng",
            data=None
        )

    # Chuẩn bị phản hồi
    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": order.order_at,
            "order_status": order.order_status,
            "response": order.response,
            "customer_address": order.customer_address,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "image_url": order.image_url,
            "shipping_status": order.shipping_status,
            "payment_status": order.payment_status,
            "items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "price": float(item.price),
                    "quantity": details.item_quantity,
                    "image_url": item.image_url,
                    "category": {
                        "category_id": item.category.category_id,
                        "category_name": item.category.category_name
                    },
                    "shop": {
                        "shop_id": item.shop.shop_id,
                        "shop_name": item.shop.shop_name,
                        "address": item.shop.address,
                        "phone": item.shop.phone
                    },
                    "color": {
                        "color_id": color.color_id,
                        "color_label": color.color_label
                    },
                    "size": {
                        "size_id": size.size_id,
                        "size_label": size.size_label
                    },
                }
                for details in order.details
                for item in db.query(Item).filter(Item.item_id == details.item_id).all()
                for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()
                for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()
            ],
            "customizations": [
                {
                    "customization_id": customization.customization_id,
                    "item_id": customization.item_id,
                    "price_adjustment": customization.price_adjustment,
                    "description": customization.description,
                    "image_url": customization.image_url,
                    "is_shop_owner_created": customization.is_shop_owner_created
                }
                for details in order.details
                for customization in db.query(Customization)
                    .filter(Customization.customization_id == details.customization_id).all()
            ]
        }
        for order in orders
    ]
    # Tính trang trước và trang kế
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    return ResponseAPI(
        status=1,
        message="Lấy đơn hàng thành công",
        data={
            "orders": order_response,
            "pagination": {
                "total_records": total_orders,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        }
    )

# API update order status 
@app.put("/orders/reject/{order_id}/status", response_model=ResponseAPI)
def update_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng",
            data=None
        )
    

    order.order_status = '0'
    order.response = "Đơn hàng đã bị từ chối"
 
    db.commit()
    return ResponseAPI(
        status=1,
        message="Cập nhật đơn hàng thành công",
        data=None
    )

# API update order status 
@app.put("/orders/accept/{order_id}/status", response_model=ResponseAPI)
def update_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng",
            data=None
        )
    

    order.order_status = '1'
 
    db.commit()
    return ResponseAPI(
        status=1,
        message="Cập nhật đơn hàng thành công",
        data=None
    )

# API update order shipping status 
@app.put("/orders/shop-confirm-shipping/{order_id}/status", response_model=ResponseAPI)
def update_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng",
            data=None
        )
    

    order.shipping_status = '0'
 
    db.commit()
    return ResponseAPI(
        status=1,
        message="Cập nhật đơn hàng thành công",
        data=None
    )

# API update order shipping status 
@app.put("/orders/user-confirm-shipping/{order_id}/status", response_model=ResponseAPI)
def update_order_status(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return ResponseAPI(
            status=-1,
            message="Không tìm thấy đơn hàng",
            data=None
        )
    

    order.shipping_status = '1'
 
    db.commit()
    return ResponseAPI(
        status=1,
        message="Cập nhật đơn hàng thành công",
        data=None
    )

@app.get("/items", response_model=ResponseAPI)
def get_all_items_by_status(
    status: bool = Query(True),  # Boolean query parameter for status
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),  # Start page from 1 (1-based index)
    limit: int = Query(10, ge=1),  # Limit for pagination
):
    skip = (page - 1) * limit

    # Query to get total number of items with the given status
    total_items = db.query(Item).filter(cast(Item.status, String) == ('1' if status else '0')).count()
    
    # Query to get the paginated items with the given status
    items = db.query(Item).filter(Item.status == ('1' if status else '0')).offset(skip).limit(limit).all()

    total_pages = (total_items + limit - 1) // limit  # Round up
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

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
            quantity=item.quantity,
            # Create a dictionary for each color using ColorCreate
            colors=[ColorDTO(color_id=color.color_id, color_label=color.color_label) 
                    for color in db.query(Color).join(ItemColors).filter(ItemColors.item_id == item.item_id).all()],
            # Create a dictionary for each size using SizeCreate
            sizes=[SizeDTO(size_id=size.size_id, size_label=size.size_label) 
                   for size in db.query(Size).join(ItemSizes).filter(ItemSizes.item_id == item.item_id).all()],
            status=item.status,
            shop= ShopDetail(
                shop_id=item.shop_id,
                shop_name=item.shop.shop_name,
                address=item.shop.address,
                phone=item.shop.phone,
                description=item.shop.description,
                status=item.shop.status
            )           
        )
        for item in items
    ]

    return ResponseAPI(
        status=1,
        message="Lấy danh sách sản phẩm thành công!",
        data={
            "items": items_response,
            "pagination": {
                "total_records": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "next_page": next_page,
                "prev_page": prev_page
            }
        }
    )


@app.get("/getRevenueByMonth/{shop_id}/{year}/{month}", response_model=ResponseAPI)
def get_getRevenueByMonthOfShop(
    shop_id: int, 
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .filter(Item.shop_id == shop_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Ensure month and year are valid and generate the start and end dates
    try:
        start_of_month = datetime(year, month, 1)
        if month == 12:  # Handle the year boundary for December
            end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)
    except ValueError:
        return ResponseAPI(
            status=-1,
            message="Invalid month or year provided.",
            data={}
        )

    # Get the number of days in the month
    num_days_in_month = (end_of_month - start_of_month).days + 1
    num_weeks_in_month = (num_days_in_month + start_of_month.weekday()) // 7 + 1

    # Initialize weeks data for all weeks in the month
    weeks_data = {f"week{week}": {"totalRevenue": 0, "orderCount": 0} for week in range(1, num_weeks_in_month + 1)}

    # Iterate over orders and group by week
    for order in order_response:
        # Convert the timestamp to datetime
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Use fromtimestamp instead of utcfromtimestamp
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Only process orders within the specified month and year
        if start_of_month <= order_date <= end_of_month:
            # Calculate the week number of the month
            delta = order_date - start_of_month
            week_number = (delta.days // 7) + 1

            week_key = f"week{week_number}"

            # Only accumulate total revenue and order count if order_status is '1'
            if order["order_status"] == '1':
                weeks_data[week_key]["totalRevenue"] += order["total_price"]
            weeks_data[week_key]["orderCount"] += 1


    # Convert the weeks_data dictionary to a list of dictionaries
    weeks_summary = [
        {"week": week, "totalRevenue": data["totalRevenue"], "orderCount": data["orderCount"]}
        for week, data in weeks_data.items()
    ]

    # Sort by week
    weeks_summary.sort(key=lambda x: x['week'])

    return ResponseAPI(
        status=1,
        message="Lấy doanh thu theo tuần thành công",
        data={
            "weeks": weeks_summary
        }
    )

@app.get("/getRevenueByMonth/{year}/{month}", response_model=ResponseAPI)
def get_getRevenueByMonthAdmin(
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Ensure month and year are valid and generate the start and end dates
    try:
        start_of_month = datetime(year, month, 1)
        if month == 12:  # Handle the year boundary for December
            end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)
    except ValueError:
        return ResponseAPI(
            status=0,
            message="Invalid month or year provided.",
            data={}
        )

    # Get the number of days in the month
    num_days_in_month = (end_of_month - start_of_month).days + 1
    num_weeks_in_month = (num_days_in_month + start_of_month.weekday()) // 7 + 1

    # Initialize weeks data for all weeks in the month
    weeks_data = {f"week{week}": {"totalRevenue": 0, "orderCount": 0} for week in range(1, num_weeks_in_month + 1)}

    # Iterate over orders and group by week
    for order in order_response:
        # Convert the timestamp to datetime
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Use fromtimestamp instead of utcfromtimestamp
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Only process orders within the specified month and year
        if start_of_month <= order_date <= end_of_month:
            # Calculate the week number of the month
            delta = order_date - start_of_month
            week_number = (delta.days // 7) + 1

            week_key = f"week{week_number}"

            # Only accumulate total revenue and order count if order_status is '1'
            if order["order_status"] == '1':
                weeks_data[week_key]["totalRevenue"] += order["total_price"]
            weeks_data[week_key]["orderCount"] += 1


    # Convert the weeks_data dictionary to a list of dictionaries
    weeks_summary = [
        {"week": week, "totalRevenue": data["totalRevenue"], "orderCount": data["orderCount"]}
        for week, data in weeks_data.items()
    ]

    # Sort by week
    weeks_summary.sort(key=lambda x: x['week'])

    return ResponseAPI(
        status=1,
        message="Lấy doanh thu theo tuần thành công",
        data={
            "weeks": weeks_summary
        }
    )


@app.get("/getRevenueByToday/{shop_id}", response_model=ResponseAPI)
def get_revenue_by_today_shop(
    shop_id: int, 
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .filter(Item.shop_id == shop_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Get today's date range
    today = datetime.now()
    start_of_today = datetime(today.year, today.month, today.day, 0, 0, 0)
    end_of_today = datetime(today.year, today.month, today.day, 23, 59, 59)

    total_revenue_today = 0
    total_orders_today = 0

  # Iterate over orders and filter for the specific day
    for order in order_response:
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Convert to datetime
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Check if the order is within the specified day range
        if start_of_today <= order_date <= end_of_today:
            # Only count the revenue if order_status is '1'
            if order['order_status'] == '1':
                total_revenue_today += order['total_price']
            total_orders_today += 1


    return ResponseAPI(
        status=1,
        message="Lấy doanh thu hôm nay thành công",
        data={
            "totalRevenueToday": total_revenue_today,
            "orderCountToday": total_orders_today
        }
    )

@app.get("/getRevenueByToday/", response_model=ResponseAPI)
def get_revenue_by_today_admin(
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Get today's date range
    today = datetime.now()
    start_of_today = datetime(today.year, today.month, today.day, 0, 0, 0)
    end_of_today = datetime(today.year, today.month, today.day, 23, 59, 59)

    total_revenue_today = 0
    total_orders_today = 0

     # Iterate over orders and filter for the specific day
    for order in order_response:
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Convert to datetime
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Check if the order is within the specified day range
        if start_of_today <= order_date <= end_of_today:
            # Only count the revenue if order_status is '1'
            if order['order_status'] == '1':
                total_revenue_today += order['total_price']
            total_orders_today += 1


    return ResponseAPI(
        status=1,
        message="Lấy doanh thu hôm nay thành công",
        data={
            "totalRevenueToday": total_revenue_today,
            "orderCountToday": total_orders_today
        }
    )

@app.get("/getRevenueByDay/{shop_id}/{day}/{month}/{year}", response_model=ResponseAPI)
def get_revenue_by_day_shop(
    shop_id: int,
    day: int,
    month: int,
    year: int,
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .filter(Item.shop_id == shop_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Get the specified day range
    try:
        start_of_day = datetime(year, month, day, 0, 0, 0)
        end_of_day = datetime(year, month, day, 23, 59, 59)
    except ValueError as e:
        return ResponseAPI(
            status=-1,
            message=f"Invalid date provided: {e}",
            data={}
        )

    total_revenue = 0
    total_orders = 0

    # Iterate over orders and filter for the specific day
    for order in order_response:
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Convert to datetime
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Check if the order is within the specified day range
        if start_of_day <= order_date <= end_of_day:
            # Only count the revenue if order_status is '1'
            if order['order_status'] == '1':
                total_revenue += order['total_price']
            total_orders += 1

    return ResponseAPI(
        status=1,
        message=f"Successfully fetched revenue for {day}/{month}/{year}",
        data={
            "totalRevenue": total_revenue,
            "orderCount": total_orders
        }
    )


@app.get("/getRevenueByDay/{day}/{month}/{year}", response_model=ResponseAPI)
def get_revenue_by_day(
    day: int,
    month: int,
    year: int,
    db: Session = Depends(get_db),
):
    # Fetching orders for the shop
    orders = (
        db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join(Item, OrderDetails.item_id == Item.item_id)
        .options(joinedload(Order.details))  # Load order details
        .order_by(Order.order_id.desc())
        .all()
    )

    order_response = [
        {
            "order_id": order.order_id,
            "total_price": float(order.total_price),
            "order_at": float(order.order_at),  # Ensure it's a float for timestamp processing
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
        }
        for order in orders
    ]

    # Get the specified day range
    try:
        start_of_day = datetime(year, month, day, 0, 0, 0)
        end_of_day = datetime(year, month, day, 23, 59, 59)
    except ValueError as e:
        return ResponseAPI(
            status=-1,
            message=f"Invalid date provided: {e}",
            data={}
        )

    total_revenue = 0
    total_orders = 0

    # Iterate over orders and filter for the specific day
    for order in order_response:
        try:
            order_date = datetime.fromtimestamp(order['order_at'])  # Convert to datetime
        except Exception as e:
            print(f"Error converting timestamp: {e}")
            continue

        # Check if the order is within the specified day range
        if start_of_day <= order_date <= end_of_day:
            # Only count the revenue if order_status is '1'
            if order['order_status'] == '1':
                total_revenue += order['total_price']
            total_orders += 1

    return ResponseAPI(
        status=1,
        message=f"Successfully fetched revenue for {day}/{month}/{year}",
        data={
            "totalRevenue": total_revenue,
            "orderCount": total_orders
        }
    )

