from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, Log
from schemas import LogsResponse
from dependencies import get_current_user_with_role
from typing import Optional

router = APIRouter()

@router.get("/logs", response_model=LogsResponse, tags=["Logs"], summary="Журнал действий (только админ)")
def get_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role("admin")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None, description="Фильтр по действию"),
    username: Optional[str] = Query(None, description="Фильтр по имени пользователя"),
):
    query = db.query(Log)
    if action:
        query = query.filter(Log.action == action)
    if username:
        query = query.filter(Log.username == username)
    total = query.count()
    logs = query.order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()
    return {"items": logs, "total": total}