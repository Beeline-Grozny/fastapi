from aiokafka import AIOKafkaProducer
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
# producer = AIOKafkaProducer(bootstrap_servers='localhost:9092')

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
            #produce from kafka

            await websocket.send_bytes(b"some")

    except Exception as e:
        print(e)


@router.post("/post_camera")
async def post_camera(
        camera: schemas.CameraCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_camera(camera= camera, db=db)

@router.get("/get_cameras")
async def get_cameras(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_cameras(db=db)


@router.get("/get_cars")
async def get_cars(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_cars(db=db)


# def mock_video():
#     i = 0
#
#
#     while True:
#         random = randint(0, 10)
#         mockdata = True if random > 9 else False
#         yield {i:mockdata}
#
#         i += 1
#
#
# video_gen = mock_video()
#
# @router.websocket("/ws/videooutput")
# async def websocket_output(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         async with aiohttp.ClientSession() as Session:
#             while True:
#                 img_file = await websocket.receive_text()
#                 # async with Session.post('http://<YOLO_server_address>', data=img_file) as resp:
#                 #     response = await resp.read()
#                 # это просто для дебага
#                 await websocket.send_text(str(next(video_gen)))
#
#     except Exception:
#         print("websocket disconnected")
#         await websocket.close()
#
# @router.websocket("/ws/videoinput")
# async def websocket_output(websocket: WebSocket):
#
#     try:
#         await websocket.accept()
#         async with aiohttp.ClientSession() as Session:
#             while True:
#                 img_file = await websocket.receive_bytes()
#                 # async with Session.post('http://<YOLO_server_address>', data=img_file) as resp:
#                 #     response = await resp.read()
#                 # это просто для дебага
#                 print(img_file)
#                 await websocket.send_text(str(next(video_gen)))
#
#     except Exception as e:
#         print(f"websocket disconnected{e}")
#         await websocket.close()
#     finally:
#         await websocket.close()
#
#
#
# async def process_video(user_id: str,building_id: str, end: int, iter: int, fps: float, db: AsyncSession) -> list:
#     i = 0
#     index = 0
#     results = []
#     while i < end:
#         rand = randint(0, 100)
#         current_time = str(timedelta(seconds=i / fps))
#         if rand > 95:
#             header = "Danger"
#             body = "Something is wrong"
#
#             results.append({"index": index, "header": header, "body": body, "current_time":current_time})
#             await dump_penalty(user_id=user_id, building_id=building_id, reason=body, grade = header, db=db)
#             index+=1
#         elif rand > 70:
#             header = "Warning"
#             body = "Just a warning"
#             results.append({"index": index, "header": header, "body": body, "current_time":current_time})
#             await dump_penalty(user_id=user_id,building_id=building_id, reason=body, grade=header, db=db)
#             index+=1
#         i += iter
#     return results
#
#
#
# @router.post("/videoinput", response_model=list, status_code=200)
# async def video_input(
#         building_id: uuid.UUID = Body(...), video: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
#     try:
#         size = int(video.size)
#         iter_size = size // 10
#         fps = 30.0  # заменить на реальную частоту кадров вашего видео
#         user_id = '649b657c-3859-4680-b478-2dceb1d4bb8f'
#         # if not user:
#         #     raise HTTPException(status_code=401, detail="Unauthorized")
#         # Получаем результаты из генератора
#         results = await process_video(user_id=user_id, building_id=building_id, end=size, iter=iter_size, fps=fps, db=db)
#
#         return results
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/video_to_ml")
# async def video_to_ml(
#         building_id: uuid.UUID = Form(...),
#         video: UploadFile = File(...),
#         db: AsyncSession = Depends(get_db)
# ):
#     try:
#         video_path = f"temp/{video.filename}"
#         with open(video_path, 'wb') as buffer:
#             shutil.copyfileobj(video.file, buffer)
#         img_id=str(uuid.uuid4())
#         frames_dir = f"temp/frames_{img_id}"
#         os.makedirs(frames_dir)
#
#         results = await services.process_video2(video_path=video_path, db=db, building_id=building_id, user_id="649b657c-3859-4680-b478-2dceb1d4bb8f",img_id=img_id)
#
#         shutil.rmtree(frames_dir)
#         os.remove(video_path)
#
#
#         return results
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/mediacatalog")
# async def media_catalog():
#     catalog = os.listdir("src/media")
#     return catalog
#
# @router.get("/imagesmock", status_code=200)
# async def images_mock(image: str):
#     print(f"src/media/{image}")
#     return FileResponse(f"src/media/{image}")
#
