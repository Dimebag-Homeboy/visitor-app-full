from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from config import SECRET_KEY, ALGORITHM
from models import User, Log
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Не авторизован")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_with_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return role_checker

def log_action(db: Session, user: Optional[User], action: str, details: str = None):
    log = Log(
        user_id=user.id if user else None,
        username=user.username if user else "system",
        action=action,
        details=details
    )
    db.add(log)
    db.commit()