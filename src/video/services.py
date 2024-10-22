import random
from pydantic import ValidationError
from sqlalchemy import select, delete, func, text
from typing import List
from uuid import uuid4, UUID
from fastapi import UploadFile, HTTPException
from fastapi.background import BackgroundTasks
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import cv2
from sqlalchemy.orm import aliased
from starlette.websockets import WebSocket

from src.video import schemas
from src.video import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
import av


# def generate_frames(rtsp_url: str, producer = None):
#     try:
#         # Открытие видеопотока
#         container = av.open(rtsp_url)
#         stream = container.streams.video[0]
#         for frame in container.decode(stream):
#             # Преобразование кадра в формат JPEG
#             img = frame.to_image()  # Получение PIL.Image
#             img_byte_arr = io.BytesIO()
#             img.save(img_byte_arr, format='JPEG')
#             print(img_byte_arr, img)
#             img_byte_arr = img_byte_arr.getvalue()
#
#             # Генерация кадра
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + img_byte_arr + b'\r\n')
#     except av.AVError as e:
#         print(f"Ошибка AVError: {e}")
#     except Exception as e:
#         print(f"Общая ошибка: {e}")

async def get_kafka_message(consumer: AIOKafkaConsumer, key: str):
    await consumer.start()
    try:
        async for message in consumer:
            if message.key.decode('utf-8') == key:
                yield message.value
    finally:
        await consumer.stop()


async def send_frames_to_kafka(producer: AIOKafkaProducer, key: str, jpeg):
    value = jpeg.tobytes()
    key = key.encode('utf-8')
    await producer.start()
    await producer.send_and_wait("video-frames", key=key, value=value)

    # await producer.send_and_wait("video-frames", jpeg.tobytes())


async def generate_frames(producer: AIOKafkaProducer, rtsp_url: str, camera_id: str) -> str:
    frame_count = 0
    try:

        video = cv2.VideoCapture(rtsp_url, apiPreference=cv2.CAP_FFMPEG)
        while True:
            ret, frame = video.read()
            if not ret:
                break

            (ret, jpeg) = cv2.imencode(".jpg", frame)
            frame_count += 1
            try:
                if frame_count % 10 == 0:  # Каждый 10-й кадр
                    await send_frames_to_kafka(producer=producer, key=camera_id, jpeg=jpeg)
            except Exception as e:
                print(f"Ошибка: {e}")
            if ret:
                yield jpeg.tobytes()
    except Exception as e:
        print(f"Ошибка: {e}")


async def get_rtsp_url(camera_id: str, db: AsyncSession):
    result = await db.execute(select(models.Camera.threadURL).where(models.Camera.id == camera_id))
    rtsp_url = result.scalar()
    print(rtsp_url)
    return rtsp_url


async def add_camera(camera: schemas.CameraCreate, db: AsyncSession):
    db_location = None
    if camera.location:
        try:
            db_location = models.Location(
                latitude=camera.location.latitude,
                longitude=camera.location.longitude
            )
            await db_location.save(db)

        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    db_camera = models.Camera(
        location_id=db_location.id if db_location else None,

        threadURL=camera.threadURL  # Предполагается, что вы переименуете threadURL в thread_url
    )

    await db_camera.save(db)
    db_statistic = models.Statistic(
        camera_id=db_camera.id,
        car_count=random.randint(0, 100),
        penalty_count=random.randint(100, 1000),
    )

    return db_camera


async def get_stats_by_camera_id(camera_id: str, db: AsyncSession):
    result = await db.execute(select(models.Statistic).where(models.Statistic.camera_id == camera_id))
    result = result.all()
    stats_array = []
    for stat in result:
        stat_dict = {
            "countToday": stat.car_count,
            "count": stat.penalty_count
        }
        stats_view = schemas.StatisticView.model_validate(stat_dict)
        stats_array.append(stats_view)

    return stats_array


async def get_cameras(db: AsyncSession):
    cameras = await db.execute(
        select(models.Camera, models.Location).join(models.Location, isouter=True).select_from(models.Camera))
    cameras = cameras.all()
    camera_views = []
    for camera, location in cameras:
        # Создайте словарь с данными камеры и локации
        camera_data = {
            "id": camera.id,
            "threadURL": camera.threadURL,
            # Убедитесь, что location сериализуется корректно
            "location": {
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None
            }
        }
        print(camera_data)
        # Валидируйте и создайте объект CameraView
        camera_view = schemas.CameraView.model_validate(camera_data)
        camera_views.append(camera_view)
    return camera_views


async def get_incidents(db: AsyncSession):
    incidents = await db.execute(
        select(models.Incident, models.Location).join(models.Camera, isouter=True).join(models.Location,
                                                                                        isouter=True).select_from(
            models.Incident))
    incidents = incidents.all()
    incidents_views = []
    for incident, location in incidents:
        # Создайте словарь с данными инцидента
        incident_data = {
            "id": incident.id,
            "car_id": incident.car_id,
            "camera_id": incident.camera_id,
            "status": incident.status,
            "description": incident.description,
            "location": {
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None
            },
            "time": incident.created_at
        }
        # Валидируйте и создайте объект IncidentView
        incident_view = schemas.IncidentView.model_validate(incident_data)
        incidents_views.append(incident_view)
    return incidents_views


async def get_reports(db: AsyncSession):
    reports = await db.execute(
        select(models.Report, models.Location).join(models.Camera, isouter=True).join(models.Location,
                                                                                      isouter=True).select_from(
            models.Report))
    reports = reports.all()
    reports_views = []
    for report, location in reports:
        # Создайте словарь с данными отчёта
        report_data = {
            "id": report.id,
            "incident_id": report.camera_id,
            "camera_id": report.camera_id,
            "car_id": report.car_id,
            "description": report.description,
            "status": report.status,
            "location": {
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None
            },
            "time": report.created_at
        }
        # Валидируйте и создайте объект ReportView
        report_view = schemas.ReportView.model_validate(report_data)
        reports_views.append(report_view)
    return reports_views


async def get_cars(db: AsyncSession):
    cars = await db.execute(
        select(models.Car, models.Location).join(models.CarCamera, isouter=True).join(models.Camera, isouter=True).join(
            models.Location, isouter=True).select_from(models.Car))
    cars = cars.all()
    cars_views = []
    for car, location in cars:
        # Создайте словарь с данными отчёта
        car_data = {
            "id": car.id,
            "owner": car.owner,
            "serial_number": car.serial_number,
            "region_id": car.region_id,
            "location": {
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None
            }
        }
        # Валидируйте и создайте объект ReportView
        car_view = schemas.CarView.model_validate(car_data)
        cars_views.append(car_view)
    return cars_views


async def add_incident(report: schemas.IncidentCreate, db: AsyncSession):
    db_report = models.Incident(

        camera_id=report.camera_id,
        car_id=report.car_id,
        description=report.description,
        status=report.status
    )
    await db_report.save(db)

    return db_report


async def add_report(report: schemas.ReportCreate, db: AsyncSession):
    db_report = models.Report(
        incident_id=report.incident_id,
        camera_id=report.camera_id,
        car_id=report.car_id,
        description=report.description,
        status=report.status
    )

    await db_report.save(db)

    return db_report


async def add_car(car: schemas.CarCreate, db: AsyncSession):
    db_car = models.Car(
        owner=car.owner,
        region_id=car.region_id,
        serial_number=car.serial_number
    )

    await db_car.save(db)

    return db_car


async def count_incidents(db: AsyncSession):
    query = text("""
        SELECT 'yellow' as color, COUNT(*) as count FROM incident WHERE status = 'yellow'
        UNION ALL
        SELECT 'red' as color, COUNT(*) as count FROM incident WHERE status = 'red'
        UNION ALL
        SELECT 'green' as color, COUNT(*) as count FROM incident WHERE status = 'green';
    """)

    result = await db.execute(query)

    count = result.all()
    print(count)
    count = {
        "yellow": count[0][1],
        "red": count[1][1],
        "green": count[2][1]
    }
    return count


async def count_incidents_by_camera_id(camera_id: UUID, db: AsyncSession):
    query = text("""
        SELECT 'yellow' as color, COUNT(*) as count FROM incident WHERE status = 'yellow' AND camera_id = :camera_id
        UNION ALL
        SELECT 'red' as color, COUNT(*) as count FROM incident WHERE status = 'red' AND camera_id = :camera_id
        UNION ALL
        SELECT 'green' as color, COUNT(*) as count FROM incident WHERE status = 'green' AND camera_id = :camera_id;
    """)

    result = await db.execute(query, {"camera_id": camera_id})

    count = result.all()
    print(count)
    count = {
        "yellow": count[0][1],
        "red": count[1][1],
        "green": count[2][1]
    }
    return count


async def detect_car(camera_id: UUID, car_id: UUID, db: AsyncSession):
    db_car_camera = models.CarCamera(
        camera_id=camera_id,
        car_id=car_id
    )

    await db_car_camera.save(db)

    return db_car_camera


async def get_cars_by_camera_id(camera_id: UUID, db: AsyncSession):
    query = select(models.Car).join(models.CarCamera, onclause=models.CarCamera.car_id == models.Car.id).where(
        models.CarCamera.camera_id == camera_id)
    cars = await db.execute(query)
    cars = cars.scalars().all()
    cars_views = []
    for car in cars:
        # Создайте словарь с данными отчёта
        car_data = {
            "id": car.id,
            "owner": car.owner,
            "serial_number": car.serial_number,
            "region_id": car.region_id
        }
        # Валидируйте и создайте объект ReportView
        car_view = schemas.CarView.model_validate(car_data)
        cars_views.append(car_view)
    return cars_views
