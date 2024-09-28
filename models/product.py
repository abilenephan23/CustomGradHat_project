from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.dialects.postgresql import JSONB

# bảng category lưu danh mục (nón, áo, banner)
class Category(Base):
       __tablename__ = "categories"

       category_id = Column(Integer, primary_key=True, index=True)
       category_name = Column(String)

       items = relationship("Item", back_populates="category")

class Item(Base):

       __tablename__ = "items"

       item_id = Column(Integer, primary_key=True, index=True)
       shop_id = Column(Integer, ForeignKey("shops.shop_id"))
       item_name = Column(String)
       category_id = Column(Integer, ForeignKey("categories.category_id"))
       price = Column(Integer)
       description = Column(String)
       image_url = Column(String)
       available_customization = Column(JSONB)
       create_at = Column(Integer)
       category = relationship("Category", back_populates="items")