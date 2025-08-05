import sys
import os
import cv2
from ultralytics import YOLO
from datetime import datetime

model = YOLO("../best.pt")  # หรือ yolov8s.pt, yolov8m.pt ตามต้องการ

image_path = sys.argv[1]  # รับ path จาก Node.js

# สร้างโฟลเดอร์สำหรับบันทึกผลลัพธ์
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"runs/detect/exp_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

# ทำ detection
results = model(image_path)

# บันทึกรูปผลลัพธ์
for i, r in enumerate(results):
    # วาด bounding boxes บนรูป
    annotated_img = r.plot()
    
    # บันทึกรูป
    output_filename = f"result_{i}.jpg"
    output_path = os.path.join(output_dir, output_filename)
    cv2.imwrite(output_path, annotated_img)
    
    print(f"Saved: {output_path}")

# แสดงผล class ที่ตรวจเจอ
for r in results:
    if r.boxes.cls is not None:
        for c in r.boxes.cls:
            print(model.names[int(c)])