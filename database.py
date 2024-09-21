from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://admin201exe:12345678@database-exe201.cxcsqkseiybf.ap-southeast-1.rds.amazonaws.com:5432/spotlight"  # Hoặc sử dụng PostgreSQL, MySQL

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