from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Table for categories (e.g., hat, shirt, banner)
class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100))  # Assuming a limit on name length

    # Relationship with Item
    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.shop_id"))
    name = Column(String(255))  # Assuming max length for item name
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    price = Column(Integer)
    description = Column(String)
    image_url = Column(String)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    category = relationship("Category", back_populates="items")
    
    # Note the plural naming for the collections
    item_colors = relationship('ItemColors', back_populates='item', cascade="all, delete-orphan")
    item_sizes = relationship("ItemSizes", back_populates="item" , cascade="all, delete-orphan")
    
    # Colors and sizes through association tables
    colors = relationship("Color", secondary="item_colors")
    sizes = relationship("Size", secondary="item_sizes")

# Association table between items and colors
class ItemColors(Base):
    __tablename__ = "item_colors"

    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    color_id = Column(Integer, ForeignKey("colors.color_id"), primary_key=True)

    # Back reference to the item
    item = relationship("Item", back_populates="item_colors")

# Association table between items and sizes
class ItemSizes(Base):
    __tablename__ = "item_sizes"

    item_id = Column(Integer, ForeignKey("items.item_id"), primary_key=True)
    size_id = Column(Integer, ForeignKey("sizes.size_id"), primary_key=True)

    # Back reference to the item
    item = relationship("Item", back_populates="item_sizes")

class Color(Base):
    __tablename__ = "colors"

    color_id = Column(Integer, primary_key=True, index=True)
    color_label = Column(String(50))  # Assuming color labels have max length

class Size(Base):
    __tablename__ = "sizes"

    size_id = Column(Integer, primary_key=True, index=True)
    size_label = Column(String(50))  # Assuming size labels have max length
