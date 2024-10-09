from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import BIT

class Order(Base):
       __tablename__ = "orders"
       order_id = Column(Integer, primary_key=True, index=True)
       customer_id = Column(Integer, ForeignKey("users.user_id"))
       quantity = Column(Integer)
       total_price = Column(Integer)
       order_at = Column(DateTime(timezone=True), server_default=func.now())
       order_status = Column(BIT(1))
       payment_id = Column(Integer, ForeignKey("payments.payment_id"))
       response = Column(String)
       img_url = Column(String)
       variation_id = Column(Integer, ForeignKey("item_variations.variation_id"))
       customization_id = Column(Integer, ForeignKey("customizations.customization_id"))

       user = relationship("User", back_populates="orders")
       item_variation = relationship("ItemVariation", back_populates="orders")
       customization = relationship("Customization", back_populates="orders")
       payment = relationship("Payment", back_populates="orders")