import io
import os
import uuid

from fastapi import FastAPI, File, Form
from fastapi.responses import FileResponse
from PIL import Image
from ultralytics import YOLO
import redis

r = redis.Redis(host="redis", decode_responses=False)
app = FastAPI()
detection_model = YOLO("app/yolov8n.pt")
segmentation_model = YOLO("app/yolov8n-seg.pt")


@app.post("/detection")
def detection(file: bytes = File(...), name: str = Form(...)) -> FileResponse:
    return use_model(detection_model, file, name)


@app.post("/segmentation")
def segmentation(file: bytes = File(...), name: str = Form(...)) -> FileResponse:
    return use_model(segmentation_model, file, name)


@app.post("/classify")
def classify(image: bytes = File(...), hash: str = Form(...)):
    bytes = io.BytesIO()
    image = Image.open(io.BytesIO(image))
    image.save(bytes, format=image.format)
    r.set(hash, bytes.getvalue())
    return {"type": "key", "confidence": {"key": 0.8, "cyphertext": 0.1, "other": 0.1}}


def use_model(model, file, name) -> FileResponse:
    id = uuid.uuid4().hex + os.path.splitext(name)[1]
    image = Image.open(io.BytesIO(file))
    image.filename = id
    result = model(source=image, save=True)
    file_path = f"{result[0].save_dir}/{result[0].path}"

    return FileResponse(file_path)
