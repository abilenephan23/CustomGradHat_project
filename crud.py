from sqlalchemy.orm import Session
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

def get_orders_by_shop(db: Session, shop_id: int):
    return db.query(OrderDetails).join(Item, Item.item_id == OrderDetails.item_id).filter(Item.shop_id == shop_id).all()