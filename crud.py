from sqlalchemy.orm import Session, joinedload
from models.product import Customization, Item
from models.order import *
from schemas import CustomizationCreate


# lấy customize theo id
def get_customization_by_id(db: Session, customization_id: int):
    return db.query(Customization).filter(Customization.customization_id == customization_id).first()

# tạo customize
def create_customizations(db: Session, customization: CustomizationCreate):
    db_customization = Customization(**customization.dict())
    db.add(db_customization)
    db.commit()
    db.refresh(db_customization)
    return db_customization

# cập nhật customize
def update_customizations(db: Session, customization_id: int, customization: CustomizationCreate):
    db_customization = get_customization_by_id(db, customization_id)
    if db_customization:
       db_customization.price_adjustment = customization.price_adjustment
       db_customization.image_url = customization.image_url
       db_customization.description = customization.description
       db.commit()
       db.refresh(db_customization)
       return db_customization
    return None

# xoá customize
def delete_customizations(db: Session, customization_id: int):
    db_customization = get_customization_by_id(db, customization_id)
    if db_customization:
       db.delete(db_customization)
       db.commit()
       return db_customization
    return None

def get_orders_by_shop(db: Session, shop_id: int, skip: int, limit: int):
    return (db.query(Order)
        .join(OrderDetails, Order.order_id == OrderDetails.order_id)
        .join( Item,  OrderDetails.item_id ==  Item.item_id)
        .filter( Item.shop_id == shop_id)
        .options(joinedload( Order.details))  # Load chi tiết đơn hàng
        .offset(skip)
        .limit(limit)
        .all())

def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return (
        db.query(Order)
        .filter(Order.customer_id == user_id)
        .options(joinedload(Order.details))
        .offset(skip)
        .limit(limit)
        .all()
    )

        