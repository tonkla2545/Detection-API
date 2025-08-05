#!/usr/bin/env python3
import sys
import os
import shutil

def main():
    print("🐍 Python script started")
    print(f"🐍 Python version: {sys.version}")
    print(f"🐍 Current working directory: {os.getcwd()}")
    print(f"🐍 Arguments: {sys.argv}")
    
    if len(sys.argv) != 2:
        print("❌ Usage: python detect.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"🐍 Input image path: {image_path}")
    
    # ตรวจสอบไฟล์รูปภาพ
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"✅ Input image exists")
    print(f"📏 File size: {os.path.getsize(image_path)} bytes")
    
    try:
        # สร้างโฟลเดอร์ผลลัพธ์
        runs_dir = os.path.join(os.getcwd(), 'runs')
        detect_dir = os.path.join(runs_dir, 'detect')
        
        # สร้างโฟลเดอร์ย่อยด้วย timestamp
        import time
        timestamp = int(time.time())
        result_dir = os.path.join(detect_dir, f'predict{timestamp}')
        
        os.makedirs(result_dir, exist_ok=True)
        print(f"📁 Created result directory: {result_dir}")
        
        # ลองใช้ YOLOv8 จริงก่อน
        try:
            print("🔍 Trying to import ultralytics...")
            from ultralytics import YOLO
            print("✅ Ultralytics imported successfully")
            
            # โหลดโมเดล
            print("🤖 Loading YOLO model...")
            model = YOLO('../best.pt')
            print("✅ YOLO model loaded")
            
            # ทำ detection
            print("🔍 Running detection...")
            results = model(image_path, 
                           save=True,
                           project=runs_dir,
                           name='detect',
                           exist_ok=True)
            
            print("✅ Detection completed")
            print(f"📊 Number of results: {len(results)}")
            
            # หาไฟล์ผลลัพธ์ที่ YOLOv8 สร้าง
            for result in results:
                if hasattr(result, 'save_dir') and result.save_dir:
                    print(f"📁 YOLO saved results to: {result.save_dir}")
                    
                # แสดงจำนวน objects ที่ detect ได้
                if hasattr(result, 'boxes') and result.boxes is not None:
                    num_detections = len(result.boxes)
                    print(f"🎯 Detected {num_detections} objects")
                    
                    # แสดงรายละเอียด classes
                    for box in result.boxes:
                        class_id = int(box.cls)
                        confidence = float(box.conf)
                        class_name = model.names[class_id]
                        print(f"  - {class_name}: {confidence:.2f}")
            
        except ImportError as e:
            print(f"⚠️ Cannot import ultralytics: {e}")
            print("📋 Using fallback: copying original image...")
            
            # ถ้าไม่มี YOLO ก็แค่คัดลอกไฟล์เดิม
            result_filename = os.path.basename(image_path)
            result_path = os.path.join(result_dir, result_filename)
            shutil.copy2(image_path, result_path)
            print(f"📋 Copied original image to: {result_path}")
            print("✅ Fallback completed (no actual detection performed)")
            
        except Exception as yolo_error:
            print(f"❌ YOLO detection failed: {yolo_error}")
            print("📋 Using fallback: copying original image...")
            
            # ถ้า YOLO error ก็แค่คัดลอกไฟล์เดิม
            result_filename = os.path.basename(image_path)
            result_path = os.path.join(result_dir, result_filename)
            shutil.copy2(image_path, result_path)
            print(f"📋 Copied original image to: {result_path}")
        
        # แสดงไฟล์ในโฟลเดอร์ผลลัพธ์
        if os.path.exists(result_dir):
            files = os.listdir(result_dir)
            print(f"📂 Files in result directory: {files}")
            for file in files:
                file_path = os.path.join(result_dir, file)
                print(f"   📄 {file} ({os.path.getsize(file_path)} bytes)")
        
        print("🎉 Script completed successfully")
        
    except Exception as e:
        print(f"❌ Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()