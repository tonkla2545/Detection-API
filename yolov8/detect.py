#!/usr/bin/env python3
import sys
import os
import shutil
import time
from datetime import datetime

def main():
    # Set environment variables for Render deployment
    os.environ['YOLO_CONFIG_DIR'] = '/tmp'
    os.environ['ULTRALYTICS_CONFIG_DIR'] = '/tmp'
    os.environ['TORCH_HOME'] = '/tmp/torch'
    os.environ['HF_HOME'] = '/tmp/huggingface'
    
    print("🐍 YOLO Detection Script Started")
    print(f"🐍 Python version: {sys.version}")
    print(f"🐍 Current working directory: {os.getcwd()}")
    print(f"🐍 Config dir: {os.environ.get('YOLO_CONFIG_DIR', 'default')}")
    
    if len(sys.argv) != 2:
        print("❌ Usage: python detect.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    print(f"🖼️ Input image: {image_path}")
    
    # ตรวจสอบไฟล์รูปภาพ
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"✅ Input image exists ({os.path.getsize(image_path)} bytes)")
    
    try:
        print("📦 Importing required packages...")
        
        # Import ultralytics
        try:
            from ultralytics import YOLO
            print("✅ Ultralytics imported successfully")
        except ImportError as e:
            print(f"❌ Cannot import ultralytics: {e}")
            print("💡 Please install: pip install ultralytics")
            
            # Fallback: copy original image
            fallback_copy(image_path)
            return
        
        # โหลดโมเดล YOLOv8
        print("🤖 Loading YOLOv8 model...")
        
        # ลำดับการลองโหลด model
        model_paths = [
            './best.pt',
            'yolov8n.pt',  # fallback to nano model
            'yolov8s.pt',  # small model
        ]
        
        model = None
        for model_path in model_paths:
            try:
                print(f"🔍 Trying to load model: {model_path}")
                
                # ถ้าเป็นไฟล์ที่มีอยู่แล้ว
                if os.path.exists(model_path):
                    model = YOLO(model_path)
                    print(f"✅ Loaded existing model: {model_path}")
                    break
                # ถ้าเป็น pretrained model จาก ultralytics
                elif model_path in ['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']:
                    try:
                        print(f"📥 Downloading pretrained model: {model_path}")
                        model = YOLO(model_path)
                        print(f"✅ Downloaded and loaded: {model_path}")
                        break
                    except Exception as download_error:
                        print(f"⚠️ Failed to download {model_path}: {download_error}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Error loading {model_path}: {e}")
                continue
        
        if model is None:
            print("❌ Could not load any YOLO model")
            print("🔄 Using fallback method...")
            fallback_copy(image_path)
            return
        
        print("✅ YOLOv8 model loaded successfully")
        
        # สร้างโฟลเดอร์ผลลัพธ์พร้อม timestamp
        runs_dir = os.path.join(os.getcwd(), 'runs')
        detect_base_dir = os.path.join(runs_dir, 'detect')
        
        # สร้าง unique subdirectory name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detect_subdir = f"predict_{timestamp}"
        final_output_dir = os.path.join(detect_base_dir, detect_subdir)
        
        print(f"📁 Output directory: {final_output_dir}")
        
        # ทำ Object Detection
        print("🔍 Running YOLOv8 detection...")
        results = model(
            image_path,
            save=True,              # บันทึกรูปผลลัพธ์
            project=runs_dir,       # โฟลเดอร์หลัก
            name=f'detect/{detect_subdir}',  # ชื่อโฟลเดอร์ย่อยแบบ nested
            exist_ok=True,          # อนุญาตให้เขียนทับ
            conf=0.25,              # confidence threshold
            verbose=True            # แสดงรายละเอียด
        )
        
        print("✅ Detection completed!")
        
        # แสดงผลลัพธ์
        total_detections = 0
        result_save_dir = None
        
        for i, result in enumerate(results):
            if hasattr(result, 'save_dir'):
                result_save_dir = str(result.save_dir)
                print(f"💾 Results saved to: {result_save_dir}")
            
            if hasattr(result, 'boxes') and result.boxes is not None:
                num_detections = len(result.boxes)
                total_detections += num_detections
                print(f"📊 Image {i+1}: Found {num_detections} objects")
                
                # แสดงรายละเอียดแต่ละ object
                for j, box in enumerate(result.boxes):
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[class_id]
                    
                    # พิกัดของ bounding box
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    print(f"  🎯 Object {j+1}: {class_name} ({confidence:.2%}) at [{int(x1)},{int(y1)},{int(x2)},{int(y2)}]")
        
        print(f"🎉 Detection Summary: {total_detections} objects detected total")
        
        # Manual verification and backup
        if result_save_dir and os.path.exists(result_save_dir):
            verify_and_backup_results(result_save_dir, image_path)
        else:
            print("⚠️ Result directory not found, using fallback")
            fallback_copy(image_path)
        
        # ตรวจสอบไฟล์ที่สร้างขึ้น
        verify_output_files(detect_base_dir)
        
    except Exception as e:
        print(f"❌ Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        print("🔄 Using fallback method...")
        fallback_copy(image_path)

def verify_and_backup_results(result_dir, original_image_path):
    """ตรวจสอบและสำรองผลลัพธ์"""
    try:
        print(f"🔍 Verifying results in: {result_dir}")
        
        if not os.path.exists(result_dir):
            print(f"⚠️ Result directory doesn't exist: {result_dir}")
            return False
        
        # ค้นหาไฟล์รูปภาพในโฟลเดอร์ผลลัพธ์
        image_files = []
        for file in os.listdir(result_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                image_files.append(file)
        
        if not image_files:
            print("⚠️ No image files found in result directory")
            return False
        
        # สำรองไฟล์ไปยังตำแหน่งที่ predictable
        backup_dir = os.path.join(os.getcwd(), 'runs', 'detect')
        os.makedirs(backup_dir, exist_ok=True)
        
        original_filename = os.path.basename(original_image_path)
        backup_path = os.path.join(backup_dir, original_filename)
        
        # คัดลอกไฟล์แรกที่พบ
        source_file = os.path.join(result_dir, image_files[0])
        shutil.copy2(source_file, backup_path)
        
        print(f"✅ Backup created: {backup_path}")
        print(f"📄 Backup size: {os.path.getsize(backup_path)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in backup: {e}")
        return False

def fallback_copy(image_path):
    """สำรองแผน: คัดลอกรูปเดิมถ้า YOLO ไม่ทำงาน"""
    try:
        runs_dir = os.path.join(os.getcwd(), 'runs')
        detect_dir = os.path.join(runs_dir, 'detect')
        
        # สร้างโฟลเดอร์หลัก
        os.makedirs(detect_dir, exist_ok=True)
        
        # สร้างโฟลเดอร์ย่อยด้วย timestamp
        timestamp = int(time.time())
        result_subdir = os.path.join(detect_dir, f'predict{timestamp}')
        os.makedirs(result_subdir, exist_ok=True)
        
        # คัดลอกรูปเดิมไปทั้งโฟลเดอร์หลักและโฟลเดอร์ย่อย
        result_filename = os.path.basename(image_path)
        
        # คัดลอกไปโฟลเดอร์หลัก (สำหรับ compatibility)
        main_result_path = os.path.join(detect_dir, result_filename)
        shutil.copy2(image_path, main_result_path)
        
        # คัดลอกไปโฟลเดอร์ย่อย (สำหรับ structure ที่ถูกต้อง)
        sub_result_path = os.path.join(result_subdir, result_filename)
        shutil.copy2(image_path, sub_result_path)
        
        print(f"📋 Fallback: Copied original image to:")
        print(f"   • Main: {main_result_path}")
        print(f"   • Sub:  {sub_result_path}")
        print("⚠️ Note: No actual object detection was performed")
        
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        sys.exit(1)

def verify_output_files(detect_dir):
    """ตรวจสอบไฟล์ที่สร้างขึ้น"""
    try:
        if not os.path.exists(detect_dir):
            print(f"⚠️ Detection directory not found: {detect_dir}")
            return
        
        print(f"📂 Contents of {detect_dir}: {os.listdir(detect_dir)}")
        
        # หาโฟลเดอร์ย่อย
        subdirs = [d for d in os.listdir(detect_dir) 
                  if os.path.isdir(os.path.join(detect_dir, d))]
        
        if not subdirs:
            print("⚠️ No result subdirectories found")
            # แสดงไฟล์ที่มีในโฟลเดอร์หลัก
            files = [f for f in os.listdir(detect_dir) 
                    if os.path.isfile(os.path.join(detect_dir, f))]
            if files:
                print(f"📄 Direct files in detect dir: {files}")
            return
        
        # เรียงตาม modified time
        subdirs.sort(key=lambda x: os.path.getmtime(os.path.join(detect_dir, x)), reverse=True)
        latest_dir = os.path.join(detect_dir, subdirs[0])
        
        print(f"📂 Latest result directory: {latest_dir}")
        
        # แสดงไฟล์ในโฟลเดอร์
        files = os.listdir(latest_dir)
        print(f"📄 Files created: {files}")
        
        for file in files:
            file_path = os.path.join(latest_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"   • {file} ({size} bytes)")
            
    except Exception as e:
        print(f"⚠️ Error verifying output: {e}")

if __name__ == "__main__":
    main()