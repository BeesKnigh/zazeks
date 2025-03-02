import cv2
from ultralytics import YOLO

# Загрузите вашу обученную модель (путь к файлу .pt)
model = YOLO(r"C:\develop\zazeks\backend\src\api\best.pt")

# Определите сопоставление номеров классов с их названиями
class_names = {0: "Paper", 1: "Rock", 2: "Scissors"}

# Открытие видеопотока (0 – вебкамера, либо можно указать путь к видеофайлу)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Не удалось получить кадр с камеры")
        break

    # Выполнение детекции на текущем кадре
    # Если требуется задать порог уверенности, можно использовать параметр conf
    results = model(frame, conf=0.4)

    # Обработка результатов
    # Результаты – это список объектов, по одному для каждого изображения
    for result in results:
        # Доступ к найденным bounding boxes
        boxes = result.boxes
        for box in boxes:
            # Получение координат ограничивающего прямоугольника
            # box.xyxy содержит координаты в формате [x1, y1, x2, y2]
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Получение значения уверенности (confidence) и номера класса (cls)
            conf = box.conf[0] if hasattr(box, 'conf') else 0
            cls = int(box.cls[0]) if hasattr(box, 'cls') else -1

            # Получение метки класса
            label = class_names.get(cls, "неизвестно")

            # Рисуем прямоугольник и текст с меткой и уверенностью
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label}: {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Отображаем кадр с детекциями
    cv2.imshow("Детекция объектов", frame)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение видеопотока и закрытие окон
cap.release()
cv2.destroyAllWindows()
