import uuid
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class ResponseMixin:
    status_code: int

class LocationView(BaseModel):
    latitude: str | None
    longitude: str | None


class CameraCreate(BaseModel):
    location: Optional[LocationView] = None

    threadURL: str




    class Config:
        orm_mode = True
        from_attributes = True


class CameraView(BaseModel):
    id: uuid.UUID
    location: Optional[LocationView] = None
    statistic: Optional[str] = None
    threadURL: str

    class Config:
        orm_mode = True
        from_attributes = True


class CarView(BaseModel):
    id: uuid.UUID
    location: Optional[LocationView] = None
    statistic: Optional[str] = None
    owner: str
    region_id: int = Field(alias="region_id", serialization_alias="regionId")
    serial_number: str = Field(alias="serial_number", serialization_alias="serialNumber")

    class Config:
        orm_mode = True
        from_attributes = True


class CarCreate(BaseModel):
    owner: str
    serial_number: str = Field(alias="serial_number", serialization_alias="serialNumber")
    region_id: int = Field(alias="region_id", serialization_alias="regionId")

    class Config:
        orm_mode = True
        from_attributes = True


class NumberData(BaseModel):
    img: str
    title: str


class StatisticView(BaseModel):
    countToday: int
    count: int


# Модель для данных номеров автомобилей
# class NumberData(BaseModel):
#     id: str
#     updated_at: datetime
#     statistic: Optional[StatisticView]
#     location: LocationView
#     threadURL: str

# Модель для отчётов
class ReportView(BaseModel):
    location: LocationView = Field(alias="location", serialization_alias="coordinates")
    description: str
    status: Literal["red", "yellow", "green"]
    created_at: datetime = Field(alias="time", serialization_alias="time")


class ReportCreate(BaseModel):
    camera_id: uuid.UUID
    car_id: uuid.UUID
    description: str
    status: Literal["red", "yellow", "green"]

# Пример использования модели
