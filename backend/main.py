import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from database import engine, Base
from routers import auth, visitors, users, logs
import models  # важно: импортируем все модели, чтобы Base.metadata знал о них
from limiter import limiter

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ С РОТАЦИЕЙ ==========
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "error.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger("visitors_app")

# ========== MIDDLEWARE ДЛЯ ЛОГИРОВАНИЯ ОШИБОК ==========
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"Unhandled exception: {request.method} {request.url}")
            raise e

# ========== ФУНКЦИИ ==========
def create_test_users():
    # Тестовые пользователи создаются всегда (убрана проверка на development)
    from sqlalchemy.orm import Session
    from database import SessionLocal
    from utils import get_password_hash
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == "admin").first():
            db.add(models.User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Администратор",
                role="admin",
                is_admin=True
            ))
        if not db.query(models.User).filter(models.User.username == "secretary").first():
            db.add(models.User(
                username="secretary",
                hashed_password=get_password_hash("secret123"),
                full_name="Секретарь Иванова",
                role="secretary",
                is_admin=False
            ))
        if not db.query(models.User).filter(models.User.username == "guard").first():
            db.add(models.User(
                username="guard",
                hashed_password=get_password_hash("guard123"),
                full_name="Охранник Петров",
                role="guard",
                is_admin=False
            ))
        db.commit()
        logger.info("Test users created/verified")
    except Exception as e:
        logger.error(f"Error creating test users: {e}")
        db.rollback()
    finally:
        db.close()

def cleanup_expired_tokens():
    try:
        with engine.connect() as conn:
            # Совместимый SQL для PostgreSQL и SQLite
            # Для SQLite используем CURRENT_TIMESTAMP, для PostgreSQL NOW()
            # Упростим: будем использовать CURRENT_TIMESTAMP, который работает в обеих СУБД
            conn.execute(text("DELETE FROM refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP OR revoked = TRUE"))
            conn.commit()
        logger.info("Expired refresh tokens cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning tokens: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Создаём таблицы, если их нет
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created.")
    # 2. Очищаем просроченные токены
    cleanup_expired_tokens()
    # 3. Создаём тестовых пользователей
    create_test_users()
    yield
    # Здесь можно добавить код для закрытия соединений при выключении

app = FastAPI(
    title="Visitor Registration API",
    description="Система регистрации посетителей",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(visitors.router)
app.include_router(users.router)
app.include_router(logs.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))