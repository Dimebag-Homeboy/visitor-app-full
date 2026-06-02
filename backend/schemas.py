from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from datetime import datetime, timezone
from typing import Optional, List
import re

def utc_to_z(dt: datetime) -> str:
    """Преобразует datetime в строку ISO с Z (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace('+00:00', 'Z')

class VisitorCreate(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    company: str = Field(..., min_length=2, max_length=100)
    whom_visit: str = Field(..., min_length=2, max_length=100)
    purpose: str = Field(..., min_length=2, max_length=200)

    @field_validator('full_name', 'whom_visit', 'purpose')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z][а-яА-ЯёЁa-zA-Z\s\-\.]+$', v):
            raise ValueError('Только буквы, пробелы, дефис и точка')
        return v.strip()

class VisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    company: str
    whom_visit: str
    purpose: str
    check_in: datetime
    check_out: Optional[datetime]

    @field_serializer('check_in', 'check_out')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        return utc_to_z(dt)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., pattern="^(admin|secretary|guard)$")

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    action: str
    details: Optional[str]
    timestamp: datetime

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime) -> str:
        return utc_to_z(dt)

class VisitorsResponse(BaseModel):
    items: List[VisitorOut]
    total: int

class LogsResponse(BaseModel):
    items: List[LogOut]
    total: int