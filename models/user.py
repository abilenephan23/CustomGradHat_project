from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    password_hash = Column(String)
    address = Column(String)
    role_id = Column(Integer, ForeignKey("roles.role_id"))

    role = relationship("Role", back_populates="users")
    shops = relationship("Shop", back_populates="owner")


class Shop(Base):
    __tablename__ = "shops"

    shop_id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String)
    address = Column(String)
    phone = Column(String)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.user_id"))

    owner = relationship("User", back_populates="shops")

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String)

    users = relationship("User", back_populates="role")