from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    status = Column(Boolean, default=False)
