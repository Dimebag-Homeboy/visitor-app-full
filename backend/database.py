from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Получаем URL базы данных из переменной окружения, которую мы зададим на Clawcloud.
# Если переменной нет, используем стандартную для локальной разработки через Docker.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@postgres:5432/visitors_db")

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"options": "-c timezone=UTC"} if DATABASE_URL.startswith("postgresql") else {"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()