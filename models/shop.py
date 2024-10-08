from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import BIT

from database import Base

class Shop(Base):
    __tablename__ = "shops"
    shop_id = Column(Integer, primary_key=True, index=True)
    status = Column(BIT(1))
    shop_name = Column(String)
    address = Column(String)
    phone = Column(String)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    owner = relationship("User", back_populates="shops")
    items = relationship("Item", back_populates="shop")
    