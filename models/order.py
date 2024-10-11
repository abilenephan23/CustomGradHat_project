from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import BIT

class Order(Base):
       __tablename__ = "orders"
       order_id = Column(Integer, primary_key=True, index=True)
       customer_id = Column(Integer, ForeignKey("users.user_id"))
       total_price = Column(Integer)
       order_at = Column(DateTime(timezone=True), server_default=func.now())
       order_status = Column(BIT(1))
       response = Column(String)
       customer_address = Column(String)
       customer_name = Column(String)
       customer_phone = Column(String)
       image_url = Column(String)
       payment_status = Column(BIT(1))
       shipping_status = Column(BIT(1))

       user = relationship("User", back_populates="orders")
       details = relationship("OrderDetails", back_populates="order")

class OrderDetails(Base):
       __tablename__ = "order_details"
       order_details_id = Column(Integer, primary_key=True, index=True)
       order_id = Column(Integer, ForeignKey("orders.order_id"))
       item_id = Column(Integer, ForeignKey("items.item_id"))
       customization_id = Column(Integer, ForeignKey("customizations.customization_id"))
       item_quantity = Column(Integer)
       color_id = Column(Integer, ForeignKey("colors.color_id"))
       size_id = Column(Integer, ForeignKey("sizes.size_id"))

       order = relationship("Order", back_populates="details")
       item = relationship("Item", back_populates="details")
       customization = relationship("Customization", back_populates="details")
