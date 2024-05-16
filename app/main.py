import io
import os
import uuid
from typing import Dict, List

import redis
from fastapi import FastAPI, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel
from ultralytics import YOLO

r = redis.Redis(host="redis", decode_responses=False)
app = FastAPI()
detection_model = YOLO("app/yolov8n.pt")
segmentation_model = YOLO("app/yolov8n-seg.pt")


@app.post("/detection")
async def detection(file: bytes = File(...), name: str = Form(...)) -> FileResponse:
    return use_model(detection_model, file, name)


@app.post("/segmentation")
async def segmentation(file: bytes = File(...), name: str = Form(...)) -> FileResponse:
    return use_model(segmentation_model, file, name)


@app.post("/classify/{hash:str}")
async def classify(hash: str, image: bytes = File(...)):
    bytes = io.BytesIO()
    image = Image.open(io.BytesIO(image))
    image.save(bytes, format=image.format)
    r.set(hash, bytes.getvalue())
    return {
        "hash": hash,
        "type": "key",
        "confidence": {"key": 0.8, "cyphertext": 0.1, "other": 0.1},
    }


@app.post("/segment_key/{hash:str}")
async def segment_key(hash: str):
    image = get_image(hash)

    return {
        "areas": [
            {"x": 0, "y": 0, "width": 100, "height": 100, "type": "basic_key"},
            {"x": 320, "y": 460, "width": 32, "height": 213, "type": "special_key"},
        ]
    }


@app.post("/segment_text/{hash:str}")
async def segment_text(hash: str):
    image = get_image(hash)

    return {
        "areas": [
            {"x": 0, "y": 0, "width": 100, "height": 100},
            {"x": 320, "y": 460, "width": 32, "height": 213},
        ]
    }


class Area(BaseModel):
    x: int
    y: int
    width: int
    height: int


class AreaList(BaseModel):
    areas: List[Area]


@app.post("/extract_key/{hash:str}")
async def extract_key(hash: str, areas: AreaList):
    image = get_image(hash)

    return {"contents": [f"Key content #{i}" for i, _ in enumerate(areas.areas)]}


@app.post("/extract_text/{hash:str}")
async def extract_text(hash: str, areas: AreaList):
    image = get_image(hash)

    return {"contents": [f"Encrypted content #{i}" for i, _ in enumerate(areas.areas)]}


def get_image(hash: str) -> bytes:
    image = r.get(hash)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not in cache"
        )

    return image


class DecryptModel(BaseModel):
    key: Dict
    text: Dict


@app.post("/decrypt")
async def decrypt(decrypt_request: DecryptModel):
    return "Decrypted content"


def use_model(model, file, name) -> FileResponse:
    id = uuid.uuid4().hex + os.path.splitext(name)[1]
    image = Image.open(io.BytesIO(file))
    image.filename = id
    result = model(source=image, save=True)
    file_path = f"{result[0].save_dir}/{result[0].path}"

    return FileResponse(file_path)
