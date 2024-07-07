import uuid
from datetime import datetime

from src.database import Base
from typing import Annotated
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime
from sqlalchemy.ext.compiler import compiles


class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


#pk_id = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime, mapped_column(server_default=utcnow(), default=utcnow())]
updated_at = Annotated[datetime, mapped_column(default=utcnow(), server_default=utcnow(), onupdate=utcnow())]
pk_id = Annotated[uuid.UUID, mapped_column(primary_key=True, index=True, default=uuid.uuid4)]


class AttributeMixin:
    id: Mapped[pk_id]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class Camera(Base, AttributeMixin):
    __tablename__ = "camera"

    location_id: Mapped[str] = mapped_column(ForeignKey("location.id"), nullable=True)

    threadURL: Mapped[str] = mapped_column(String(255), nullable=False)



class Location(Base, AttributeMixin):
    __tablename__ = "location"

    latitude: Mapped[str] = mapped_column(String(255), nullable=False)
    longitude: Mapped[str] = mapped_column(String(255), nullable=False)


class Statistic(Base, AttributeMixin):
    __tablename__ = "statistic"
    camera_id: Mapped[str] = mapped_column(ForeignKey("camera.id"), nullable=False)
    car_count: Mapped[int] = mapped_column(String(255), nullable=False, default=0, server_default="0")
    penalty_count: Mapped[int] = mapped_column(String(255), nullable=False, default=0, server_default="0")
    violation_count: Mapped[int] = mapped_column(String(255), nullable=False, default=0, server_default="0")



class Incident(Base, AttributeMixin):
    __tablename__ = "incident"
    camera_id: Mapped[str] = mapped_column(ForeignKey("camera.id"), nullable=False)
    car_id: Mapped[str] = mapped_column(ForeignKey("car.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)

class Report(Base, AttributeMixin):
    __tablename__ = "report"
    """
    coordinates: LocationView
    description: str
    status: Literal["red", "yellow", "green"]
    time: datetime    
    """
    incident_id: Mapped[str] = mapped_column(ForeignKey("incident.id"), nullable=False)
    camera_id: Mapped[str] = mapped_column(ForeignKey("camera.id"), nullable=False)
    car_id: Mapped[str] = mapped_column(ForeignKey("car.id"), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)


class CarCamera(Base, AttributeMixin):
    __tablename__ = "car_camera"

    camera_id: Mapped[str] = mapped_column(ForeignKey("camera.id"), nullable=False)
    car_id: Mapped[str] = mapped_column(ForeignKey("car.id"), nullable=False)
class Car(Base, AttributeMixin):
    __tablename__ = "car"

    serial_number: Mapped[str] = mapped_column(String(255), nullable=False)
    region_id: Mapped[int] = mapped_column(nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)