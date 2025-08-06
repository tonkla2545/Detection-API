#!/usr/bin/env python3
import sys
import os
import shutil
import time
import signal
from datetime import datetime

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Detection timeout!")

def main():
    # Set environment variables
    os.environ['YOLO_CONFIG_DIR'] = '/tmp'
    os.environ['ULTRALYTICS_CONFIG_DIR'] = '/tmp'
    os.environ['TORCH_HOME'] = '/tmp/torch'
    
    if len(sys.argv) != 2:
        print("❌ Usage: python detect.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # ตรวจสอบไฟล์รูปภาพ
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"🖼️ Processing: {image_path} ({os.path.getsize(image_path)} bytes)")
    
    try:
        # Import และโหลดโมเดล
        from ultralytics import YOLO
        
        # ลำดับโหลดโมเดล (สั้นๆ)
        model_paths = [
            './yolov8/best.pt',
            '../../server/yolov8/best.pt', 
            './best.pt',
            'yolov8n.pt'
        ]
        
        model = None
        for model_path in model_paths:
            try:
                if os.path.exists(model_path) or model_path.endswith('n.pt'):
                    model = YOLO(model_path)
                    print(f"✅ Loaded: {model_path}")
                    break
            except Exception as e:
                continue
        
        if model is None:
            print("❌ No model loaded, using fallback")
            fallback_copy(image_path)
            return
        
        # เตรียมโฟลเดอร์ output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"runs/detect/predict_{timestamp}"
        
        # ทำ Detection พร้อม timeout
        print("🔍 Running detection...")
        
        try:
            # ตั้ง timeout 45 วินาที
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(45)
            
            results = model(
                image_path,
                save=True,
                project='runs',
                name=f'detect/predict_{timestamp}',
                exist_ok=True,
                conf=0.3,
                imgsz=640,
                device='cpu',
                verbose=False,  # ปิด verbose ลดข้อความ
                max_det=50
            )
            
            signal.alarm(0)  # ปิด alarm
            print("✅ Detection completed!")
            
            # แสดงผลลัพธ์แบบสั้น
            total_detections = 0
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    total_detections += len(result.boxes)
                    for i, box in enumerate(result.boxes[:3]):  # แสดงแค่ 3 ตัวแรก
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = model.names[class_id]
                        print(f"  🎯 {class_name} ({confidence:.1%})")
                    
                    if len(result.boxes) > 3:
                        print(f"  ... และอีก {len(result.boxes) - 3} objects")
            
            print(f"🎉 Total: {total_detections} objects")
            
            # Backup ไฟล์
            backup_results(output_dir, image_path)
            
        except TimeoutError:
            print("⏰ Detection timeout - using fallback")
            signal.alarm(0)
            fallback_copy(image_path)
            
        except Exception as e:
            print(f"❌ Detection error: {str(e)[:100]}...")
            fallback_copy(image_path)
        
    except ImportError:
        print("❌ Ultralytics not available - using fallback")
        fallback_copy(image_path)
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}...")
        fallback_copy(image_path)

def backup_results(output_dir, original_image_path):
    """สำรอง result ไปตำแหน่งหลัก"""
    try:
        # หาไฟล์ result
        full_output_dir = os.path.join(os.getcwd(), output_dir)
        if os.path.exists(full_output_dir):
            image_files = [f for f in os.listdir(full_output_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if image_files:
                # คัดลอกไป main detect folder
                main_detect_dir = 'runs/detect'
                os.makedirs(main_detect_dir, exist_ok=True)
                
                source_file = os.path.join(full_output_dir, image_files[0])
                backup_file = os.path.join(main_detect_dir, os.path.basename(original_image_path))
                shutil.copy2(source_file, backup_file)
                print(f"💾 Saved: {backup_file}")
                return True
    except Exception as e:
        print(f"⚠️ Backup failed: {e}")
        return False

def fallback_copy(image_path):
    """คัดลอกรูปเดิมเมื่อ detection ล้มเหลว"""
    try:
        # สร้าง output directory
        timestamp = int(time.time())
        result_dir = f'runs/detect/predict{timestamp}'
        os.makedirs(result_dir, exist_ok=True)
        
        # สร้าง main detect directory
        main_detect_dir = 'runs/detect'
        os.makedirs(main_detect_dir, exist_ok=True)
        
        filename = os.path.basename(image_path)
        
        # คัดลอกไปทั้ง 2 ที่
        shutil.copy2(image_path, os.path.join(result_dir, filename))
        shutil.copy2(image_path, os.path.join(main_detect_dir, filename))
        
        print(f"📋 Fallback: {filename}")
        
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()