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

@router.websocket("/ws/{camera_id}")
async def websocket_output(websocket: WebSocket, camera_id: str, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            cunsume = await services.get_kafka_message(camera_id, db)

            await websocket.send_bytes(b"some")

    except Exception as e:
        print(e)


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
@router.post("/post_car_number")
async def post_car_number(
    car_id:UUID,
    camera_id:UUID,
    db: AsyncSession = Depends(get_db)
):
    return await services.detect_car(car_id=car_id, camera_id=camera_id, db=db)
