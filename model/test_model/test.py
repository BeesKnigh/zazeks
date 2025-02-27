from ultralytics import YOLO

model = YOLO(r"C:\develop\zazeks\model\learning\runs\detect\train4\weights\best.pt")

img_np = r'C:\develop\zazeks\model\test_model\images.jpg'

results = model.predict(source=img_np, device="cpu", conf=0.4)

for result in results:
    boxes = result.boxes  # Boxes object for bounding box outputs
    masks = result.masks  # Masks object for segmentation masks outputs
    keypoints = result.keypoints  # Keypoints object for pose outputs
    probs = result.probs  # Probs object for classification outputs
    obb = result.obb  # Oriented boxes object for OBB outputs
    result.show()  # display to screen
    result.save(filename="result.jpg")  # save to disk