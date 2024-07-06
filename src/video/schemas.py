from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResponseMixin:
    status_code: int


class CameraCreate(BaseModel):
    location: Optional[dict] = None
    statistic: Optional[str] = None
    threadURL: str


class LocationView(BaseModel):
    latitude: str
    longitude: str

class CameraView(BaseModel):
    id: str
    location: Optional[LocationView] = None
    statistic: Optional[str] = None
    threadURL: str
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True
        from_attributes = True
