from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import Token, UserOut
from utils import verify_password, create_access_token, create_refresh_token, get_refresh_token, revoke_refresh_token
from dependencies import log_action, get_current_user
import os
from limiter import limiter

router = APIRouter()

COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60
COOKIE_PATH = "/"
COOKIE_HTTPONLY = True
COOKIE_SECURE = os.getenv("ENVIRONMENT", "development") == "production"
COOKIE_SAMESITE = "strict"

def set_refresh_token_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

def clear_refresh_token_cookie(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path=COOKIE_PATH)

@router.post("/token", response_model=Token, tags=["Authentication"], summary="Вход в систему")
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(user.id, db)
    set_refresh_token_cookie(response, refresh_token)
    log_action(db, user, "login", "Вход в систему")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
    }

@router.post("/refresh", response_model=Token, tags=["Authentication"], summary="Обновление access-токена")
def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # CSRF проверка ТОЛЬКО не в тестах
    if os.getenv("ENVIRONMENT") != "test":
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        allowed_hosts = ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost"]
        valid = False
        if origin and origin in allowed_hosts:
            valid = True
        if referer and any(referer.startswith(host) for host in allowed_hosts):
            valid = True
        if not valid:
            raise HTTPException(status_code=403, detail="CSRF check failed")

    refresh_token = request.cookies.get(COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found in cookie")
    rt = get_refresh_token(db, refresh_token)
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = db.query(User).filter(User.id == rt.user_id).first()
    if not user:
        raise HTTPException(status_code=401)
    new_access_token = create_access_token(data={"sub": user.username})
    revoke_refresh_token(db, refresh_token)
    new_refresh_token = create_refresh_token(user.id, db)
    set_refresh_token_cookie(response, new_refresh_token)
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name,
    }

@router.post("/logout", tags=["Authentication"], summary="Выход из системы")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clear_refresh_token_cookie(response)
    return {"message": "Logged out"}

@router.get("/users/me", response_model=UserOut, tags=["Users"], summary="Текущий пользователь")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user