import asyncio
from uuid import UUID

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi.responses import StreamingResponse, Response
from fastapi import BackgroundTasks, File, UploadFile, APIRouter, Body, Form, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.video import schemas
from src.video import services

router = APIRouter(
    prefix="/camera_api",
    tags=["camera_api"],
    responses={404: {"description": "Not found"}},
)
producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')
consumer = AIOKafkaConsumer('photo normalization', bootstrap_servers='localhost:9092', group_id='photo normalization')


@router.get("/stream_rtsp/{camera_id}")
async def get_rtsp(
        camera_id: str,
        db: AsyncSession = Depends(get_db)
):
    #rtsp_url = "rtsp://807e9439d5ca.entrypoint.cloud.wowza.com:1935/app-rC94792j/068b9c9a_stream2"
    rtsp_url = await services.get_rtsp_url(camera_id, db)
    return StreamingResponse(services.generate_frames(rtsp_url, producer=None), media_type="multipart/x-mixed-replace; boundary=frame", status_code=206)

@router.get("/statistic_of_camera/{camera_id}")
async def get_statistic(
        camera_id: str,
        db: AsyncSession = Depends(get_db)
):
    return await services.get_stats_by_camera_id(camera_id, db)
# @router.websocket("/ws/{camera_id}")
# async def websocket_output(websocket: WebSocket, camera_id: str, db: AsyncSession = Depends(get_db)):
#     await websocket.accept()
#     try:
#         while True:
#             cunsume = await services.get_kafka_message(camera_id, db)
#
#             await websocket.send_bytes(b"some")
#
#     except Exception as e:
#         print(e)

@router.websocket("/ws/{camera_id}")
async def websocket_video_stream(websocket: WebSocket, camera_id: str, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    rtsp_url = await get_rtsp(camera_id, db)
    print(rtsp_url)
    async for frame in services.generate_frames(rtsp_url, producer):
        await websocket.send_bytes(frame)  # Отправка кадра через вебсокет
        await asyncio.sleep(1/30)

@router.post("/post_camera")
async def post_camera(
        camera: schemas.CameraCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_camera(camera=camera, db=db)

@router.get("/get_cameras", response_model=list[schemas.CameraView])
async def get_cameras(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_cameras(db=db)


@router.get("/get_cars", response_model=list[schemas.CarView])
async def get_cars(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_cars(db=db)

@router.get("/get_reports/", response_model=list[schemas.ReportView])
async def get_reports(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_reports(db=db)
@router.get("/get_incidents/", response_model=list[schemas.IncidentView])
async def get_reports(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_incidents(db=db)

@router.post("/post_report")
async def post_report(
        report: schemas.ReportCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_report(report=report, db=db)

@router.post("/post_incident")
async def post_report(
        report: schemas.IncidentCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_incident(report=report, db=db)


@router.post("/post_car")
async def post_car(
        car: schemas.CarCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_car(car=car, db=db)
@router.post("/bind_car_camera")
async def post_car_number(
    car_id:UUID,
    camera_id:UUID,
    db: AsyncSession = Depends(get_db)
):
    return await services.detect_car(car_id=car_id, camera_id=camera_id, db=db)

@router.get("/get_statistic")
async def get_statistic(
    db: AsyncSession = Depends(get_db)
):
    return await services.count_incidents(db=db)
@router.get("/get_statistic_by_camera/{camera_id}")
async def get_statistic_by_car(
    camera_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await services.count_incidents_by_camera_id(camera_id=camera_id, db=db)

@router.get("/get_cars_by_camera/{camera_id}")
@router.get("/get_cars/{camera_id}")
async def get_cars(
    camera_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await services.get_cars_by_camera_id(camera_id=camera_id, db=db)

@router.get("/get_linear_graf/")
async def get_incidents_by_camera(
    db: AsyncSession = Depends(get_db)
):
    return [
    { "time": "2024-07-06T00:00:00", "value": 42, "category": "легковой" },
    { "time": "2024-07-06T01:00:00", "value": 35, "category": "грузовой" },
    { "time": "2024-07-06T02:00:00", "value": 28, "category": "автобус" },
    { "time": "2024-07-06T03:00:00", "value": 47, "category": "легковой" },
    { "time": "2024-07-06T04:00:00", "value": 55, "category": "грузовой" },
    { "time": "2024-07-06T05:00:00", "value": 22, "category": "автобус" },
    { "time": "2024-07-06T06:00:00", "value": 31, "category": "легковой" },
    { "time": "2024-07-06T07:00:00", "value": 41, "category": "грузовой" },
    { "time": "2024-07-06T08:00:00", "value": 38, "category": "автобус" },
    { "time": "2024-07-06T09:00:00", "value": 29, "category": "легковой" },
    { "time": "2024-07-06T10:00:00", "value": 44, "category": "грузовой" },
    { "time": "2024-07-06T11:00:00", "value": 36, "category": "автобус" },
    { "time": "2024-07-06T12:00:00", "value": 27, "category": "легковой" },
    { "time": "2024-07-06T13:00:00", "value": 50, "category": "грузовой" },
    { "time": "2024-07-06T14:00:00", "value": 33, "category": "автобус" },
    { "time": "2024-07-06T15:00:00", "value": 42, "category": "легковой" },
    { "time": "2024-07-06T16:00:00", "value": 35, "category": "грузовой" },
    { "time": "2024-07-06T17:00:00", "value": 28, "category": "автобус" },
    { "time": "2024-07-06T18:00:00", "value": 47, "category": "легковой" },
    { "time": "2024-07-06T19:00:00", "value": 55, "category": "грузовой" },
    { "time": "2024-07-06T20:00:00", "value": 22, "category": "автобус" },
    { "time": "2024-07-06T21:00:00", "value": 31, "category": "легковой" },
    { "time": "2024-07-06T22:00:00", "value": 41, "category": "грузовой" },
    { "time": "2024-07-06T23:00:00", "value": 38, "category": "автобус" }
]

@router.get("/get_round_graf/")
async def get_round_graf(
    db: AsyncSession = Depends(get_db)
):
    return [
  {
    "type": "Положительно",
    "value": 92.1,
  },
  {
    "type": "Отрицательно",
    "value": 7.9
  }
]