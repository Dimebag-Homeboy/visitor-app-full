from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, RefreshToken
from schemas import UserCreate, UserOut
from dependencies import get_current_user_with_role, log_action
from utils import get_password_hash

router = APIRouter()

@router.get("/users", response_model=list[UserOut], tags=["Users"], summary="Список всех пользователей")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_with_role("admin"))):
    return db.query(User).all()

@router.post("/users", tags=["Users"], summary="Создание пользователя")
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role("admin"))
):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Уже существует")
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        is_admin=(user.role == 'admin')
    )
    db.add(new_user)
    db.commit()
    log_action(db, current_user, "create_user", f"Создан пользователь {user.username} (роль {user.role})")
    return {"message": "Пользователь создан"}

@router.delete("/users/{user_id}", tags=["Users"], summary="Удаление пользователя")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Нельзя удалить admin")
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    log_action(db, current_user, "delete_user", f"Удалён пользователь {user.username}")
    return {"message": "Удалён"}

@router.put("/users/{user_id}/role", tags=["Users"], summary="Изменение роли пользователя")
def change_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role("admin"))
):
    if role not in ['admin', 'secretary', 'guard']:
        raise HTTPException(status_code=400, detail="Неверная роль")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    if user.username == "admin" and role != 'admin':
        raise HTTPException(status_code=400, detail="Нельзя изменить роль admin")
    old_role = user.role
    user.role = role
    user.is_admin = (role == 'admin')
    db.commit()
    log_action(db, current_user, "change_role", f"Изменена роль пользователя {user.username}: {old_role} -> {role}")
    return {"message": "Роль обновлена"}