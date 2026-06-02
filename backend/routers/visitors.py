from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Visitor, User
from schemas import VisitorCreate, VisitorOut, VisitorsResponse
from dependencies import get_current_user, get_current_user_with_role, log_action
from utils import ensure_utc
from datetime import datetime, timezone
from typing import Optional
import openpyxl
import io
from fastapi.responses import StreamingResponse
from zoneinfo import ZoneInfo

router = APIRouter()

def apply_visitor_filters(query, search: Optional[str], hide_completed: bool, date_from: Optional[datetime], date_to: Optional[datetime]):
    if hide_completed:
        query = query.filter(Visitor.check_out == None)
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (func.lower(Visitor.full_name).like(search_term)) |
            (func.lower(Visitor.company).like(search_term)) |
            (func.lower(Visitor.whom_visit).like(search_term)) |
            (func.lower(Visitor.purpose).like(search_term))
        )
    if date_from:
        query = query.filter(Visitor.check_in >= date_from)
    if date_to:
        query = query.filter(Visitor.check_in <= date_to)
    return query

@router.post("/visitors", response_model=VisitorOut, tags=["Visitors"], summary="Регистрация нового посетителя")
def create_visitor(
    visitor: VisitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт запись о входе посетителя. Доступно для секретаря и администратора.
    Запрещено создавать активного посетителя с тем же ФИО.
    """
    existing = db.query(Visitor).filter(Visitor.full_name == visitor.full_name, Visitor.check_out == None).first()
    if existing:
        raise HTTPException(status_code=400, detail="Посетитель с таким ФИО уже на территории")
    new_visitor = Visitor(**visitor.model_dump())
    db.add(new_visitor)
    db.commit()
    db.refresh(new_visitor)
    log_action(db, current_user, "create_visitor", f"Зарегистрирован посетитель {new_visitor.full_name} (компания {new_visitor.company})")
    return VisitorOut.model_validate(new_visitor)

@router.get("/visitors", response_model=VisitorsResponse, tags=["Visitors"], summary="Список посетителей с фильтрацией и пагинацией")
def get_visitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = Query(None, description="Поиск по ФИО, компании, кому, цели"),
    hide_completed: bool = Query(False, description="Скрыть завершённые визиты"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    date_from = ensure_utc(date_from)
    date_to = ensure_utc(date_to)
    query = db.query(Visitor)
    query = apply_visitor_filters(query, search, hide_completed, date_from, date_to)
    total = query.count()
    visitors = query.order_by(Visitor.check_in.desc()).offset(skip).limit(limit).all()
    return {"items": visitors, "total": total}

@router.put("/visitors/{visitor_id}/checkout", tags=["Visitors"], summary="Отметить выход посетителя")
def checkout_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role("guard"))
):
    """Устанавливает время выхода. Доступно для охраны и администратора."""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Не найден")
    if visitor.check_out:
        raise HTTPException(status_code=400, detail="Уже отмечен")
    visitor.check_out = datetime.now(timezone.utc)
    db.commit()
    log_action(db, current_user, "checkout", f"Отметил выход посетителя {visitor.full_name}")
    return {"message": "Выход отмечен"}

@router.get("/report/excel", tags=["Reports"], summary="Выгрузка отчёта Excel")
def get_excel_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None),
    hide_completed: bool = Query(False),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """
    Формирует Excel-файл с отфильтрованным списком посетителей.
    Время приводится к Московскому (Europe/Moscow). Доступно для секретаря и администратора.
    """
    if current_user.role not in ['admin', 'secretary']:
        raise HTTPException(status_code=403, detail="Нет прав")
    date_from = ensure_utc(date_from)
    date_to = ensure_utc(date_to)
    query = db.query(Visitor)
    query = apply_visitor_filters(query, search, hide_completed, date_from, date_to)
    visitors = query.order_by(Visitor.check_in.desc()).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Посетители"
    ws.append(["ID", "ФИО", "Компания", "К кому", "Цель", "Время прихода (МСК)", "Время ухода (МСК)"])

    msk = ZoneInfo("Europe/Moscow")
    for v in visitors:
        check_in_local = v.check_in.astimezone(msk).strftime("%Y-%m-%d %H:%M:%S") if v.check_in else ""
        check_out_local = v.check_out.astimezone(msk).strftime("%Y-%m-%d %H:%M:%S") if v.check_out else ""
        ws.append([
            v.id, v.full_name, v.company, v.whom_visit, v.purpose,
            check_in_local,
            check_out_local
        ])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=visitors_report.xlsx"})