import sys
import os
from ultralytics import YOLO
import cv2

def main():
    if len(sys.argv) != 2:
        print("Usage: python detect.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # ตรวจสอบไฟล์รูปภาพ
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    try:
        # โหลดโมเดล YOLOv8
        model = YOLO('../best.pt')  # หรือใช้โมเดลที่คุณต้องการ
        
        # กำหนดโฟลเดอร์สำหรับบันทึกผลลัพธ์
        project_dir = os.path.join(os.getcwd(), 'runs')
        
        print(f"Input image: {image_path}")
        print(f"Saving results to: {project_dir}")
        
        # ทำ detection
        results = model(image_path, 
                       save=True,           # บันทึกรูปผลลัพธ์
                       project=project_dir, # โฟลเดอร์หลัก
                       name='detect',       # ชื่อโฟลเดอร์ย่อย
                       exist_ok=True)       # อนุญาตให้เขียนทับ
        
        # แสดงผลลัพธ์
        for i, result in enumerate(results):
            # นับจำนวน object ที่ detect ได้
            num_detections = len(result.boxes) if result.boxes is not None else 0
            print(f"Detected {num_detections} objects")
            
            # แสดงรายละเอียด class ที่ detect ได้
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls)
                    confidence = float(box.conf)
                    class_name = model.names[class_id]
                    print(f"- {class_name}: {confidence:.2f}")
            
            # แสดงเส้นทางไฟล์ผลลัพธ์
            if hasattr(result, 'save_dir') and result.save_dir:
                print(f"Result saved to: {result.save_dir}")
        
        print("Detection completed successfully")
        
    except Exception as e:
        print(f"Error during detection: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()