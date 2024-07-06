import io
import shutil
import uuid
from datetime import timedelta
from enum import Enum
from pathlib import Path
from random import randint
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import ValidationError

import pydantic
from sqlalchemy import select, delete
from typing import List
from uuid import uuid4

from fastapi import UploadFile, HTTPException
from fastapi.background import BackgroundTasks
from aiokafka import AIOKafkaProducer
import asyncio
import cv2
from src.video import schemas
from src.video import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert


import av

# def generate_frames(rtsp_url: str):
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


async def send_frames_to_kafka(frame, producer, jpeg):
    pass


    # await producer.send_and_wait("video-frames", jpeg.tobytes())

async def generate_frames(rtsp_url: str, producer) -> str:
    frame_count = 0
    try:
        video = cv2.VideoCapture(rtsp_url)
        video.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        print(video)
        while True:
            ret, frame = video.read()
            print(ret, frame)
            if not ret:
                break

            (ret, jpeg) = cv2.imencode(".jpg", frame)
            frame_count += 1
            if frame_count % 10 == 0:  # Каждый 10-й кадр
                await send_frames_to_kafka(frame, producer, jpeg)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + bytearray(jpeg) + b'\r\n')
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
                latitude=camera.location.get("latitude"),
                longitude=camera.location.get("longitude")
            )
            db.add(db_location)
            await db.commit()
            await db.refresh(db_location)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    db_camera = models.Camera(
        location_id=db_location.id if db_location else None,
        statistic=camera.statistic,
        threadURL=camera.threadURL  # Предполагается, что вы переименуете threadURL в thread_url
    )

    db.add(db_camera)
    try:
        await db.commit()
        await db.refresh(db_camera)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return db_camera

async def get_cameras(db: AsyncSession):
    query = select(models.Camera, models.Location.latitude, models.Location.longitude).join(models.Location, isouter=True).select_from(models.Camera)
    result = await db.execute(query)
    return result.scalars().all()
# def rand_danger():
#     rint = randint(0, 10)
#     danger = {
#         1: "Нет каски",
#         2: "Техника безопасности нарушена",
#         3: "Виден неправильный свет",
#         4: "Трещины",
#         5: "Работа с видео невозможна",
#         6: "кадр невидимый",
#         7: "Техника безопасности не выполняется",
#         8: "Техника безопасности не выполняется",
#         9: "Техника безопасности не выполняется",
#         10:"Техника безопасности не выполняется",
#     }
#     return danger[rint]
# def rand_warning():
#     rint = randint(0, 10)
#     warning = {
#         1: "Подозрительное видео",
#         2: "Плохое видео",
#         3: "Не видно",
#         4: "Цвет не определен",
#         5: "Техника безопасности не выполняется",
#         6: "Кадр невидимый",
#         7: "Плохоее разрешение",
#         8: "Техника безопасности не выполняется",
#         9: "Техника безопасности не выполняется",
#         10: "Техника безопасности не выполняется",
#     }
#     return warning[rint]

# async def bind_penalty(db: AsyncSession, penalty, building_id: uuid4):
#     stmt = insert(PenaltyBuildingModel).values(penalty_id=penalty.id, building_id=building_id)
#     await db.execute(stmt)
#     await db.commit()
#
#
# async def dump_penalty(db: AsyncSession, building_id: uuid4, user_id: uuid4, reason: str, grade: str):
#     penalty = PenaltyModel(user_id=user_id, reason=reason, grade=grade)
#     db.add(penalty)
#
#     await db.commit()
#     await bind_penalty(db=db, penalty=penalty, building_id=building_id)
#
#
# async def process_video2(user_id: uuid.UUID, building_id: uuid.UUID, video_path: str, img_id: str, db: AsyncSession) -> list:
#     index = 0
#     results = []
#
#     # Открываем видео файл с помощью OpenCV
#     cap = cv2.VideoCapture(video_path)
#
#     if not cap.isOpened():
#         raise HTTPException(status_code=500, detail="Не удалось открыть видеофайл.")
#
#     fps = cap.get(cv2.CAP_PROP_FPS)
#
#     if fps == 0:
#         raise HTTPException(status_code=500, detail="Не удалось получить FPS из видеофайла.")
#
#     frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#
#     if frame_count == 0:
#         raise HTTPException(status_code=500, detail="Не удалось получить количество кадров из видеофайла.")
#
#     duration_seconds = frame_count / fps
#
#     # Создание директории для хранения кадров (если она не существует)
#     frames_dir = Path(f"temp/frames_{img_id}")
#     frames_dir.mkdir(parents=True, exist_ok=True)
#
#     for i in range(int(duration_seconds)):
#         # Устанавливаем позицию на каждую секунду
#         set_pos_success = cap.set(cv2.CAP_PROP_POS_MSEC, i * 1000)
#
#         if not set_pos_success:
#             print(f"Не удалось установить позицию на {i} секунде.")
#             continue
#
#         ret, frame = cap.read()
#
#         if not ret or frame is None or frame.size == 0:
#             print(f"Не удалось прочитать кадр {i}.")
#             continue
#
#         # Записываем кадр из видео на диск
#         frame_path = frames_dir / f"frame_{i}.png"
#         cv2.imwrite(str(frame_path), frame)
#
#         rand = randint(0, 100)
#         current_time = timedelta(seconds=i).__str__()
#
#         header = ''
#         body = ''
#
#         if rand > 95:
#             header = "Danger"
#             body = rand_warning()
#
#         elif rand > 70:
#             header = "Warning"
#             body = rand_danger()
#
#         if rand > 70:
#             results.append({"index": index, "header": header, "body": body, "current_time": current_time})
#
#             await dump_penalty(db=db, user_id=user_id, building_id=building_id, reason=body, grade=header)
#
#
#         index += 1
#
#     cap.release()
#     return results
