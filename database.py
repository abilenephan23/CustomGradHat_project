from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')

SQLALCHEMY_DATABASE_URL = database_url  # Hoặc sử dụng PostgreSQL, MySQL

# Tạo engine kết nối với cơ sở dữ liệu PostgreSQL (loại bỏ check_same_thread)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Tạo session để tương tác với cơ sở dữ liệu
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tạo lớp cơ sở cho các models
Base = declarative_base()

# Dependency để sử dụng session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()