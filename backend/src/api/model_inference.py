from fastapi import APIRouter, File, UploadFile, HTTPException
import cv2
import numpy as np
from ultralytics import YOLO

router = APIRouter()

# Загрузка модели YOLO (укажите корректный путь к файлу best.pt)
model = YOLO("src/api/best.pt")
# Определяем соответствие номеров классов жестам
class_names = {0: "Paper", 1: "Rock", 2: "Scissors"}

@router.post("/detect", tags=["Model"])
async def detect(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Неверное изображение")

        results = model(frame, conf=0.4)
        gesture = "No detection"  # Значение по умолчанию
        bbox = []  # по умолчанию пустой список

        for result in results:
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                box = boxes[0]
                cls = int(box.cls[0])
                gesture = class_names.get(cls, "Unknown")
                # Получаем координаты bbox и приводим к целым числам
                bbox = list(map(int, box.xyxy[0].tolist()))
                break

        return {"gesture": gesture, "bbox": bbox}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

