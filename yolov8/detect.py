#!/usr/bin/env python3
import sys
import os
import shutil
import time
import signal
from datetime import datetime
from PIL import Image
import io

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Detection timeout!")

def resize_image_if_needed(image_path, max_size_mb=2, max_dimension=1280):
    """ลดขนาดรูปภาพหากใหญ่เกินไป"""
    try:
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        
        if file_size_mb <= max_size_mb:
            return image_path, False  # ไม่ต้องลดขนาด
        
        print(f"📐 Resizing large image ({file_size_mb:.1f}MB)")
        
        # สร้างไฟล์ชั่วคราว
        temp_path = f"/tmp/resized_{int(time.time())}.jpg"
        
        with Image.open(image_path) as img:
            # คำนวณขนาดใหม่
            width, height = img.size
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # Resize รูป
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # บันทึกด้วยคุณภาพที่เหมาะสม
                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')
                
                img_resized.save(temp_path, 'JPEG', quality=85, optimize=True)
                
                new_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
                print(f"✅ Resized: {width}x{height} → {new_width}x{new_height} ({new_size_mb:.1f}MB)")
                
                return temp_path, True
        
        return image_path, False
        
    except Exception as e:
        print(f"⚠️ Resize failed: {e}")
        return image_path, False

def main():
    # Set environment variables
    os.environ['YOLO_CONFIG_DIR'] = '/tmp'
    os.environ['ULTRALYTICS_CONFIG_DIR'] = '/tmp'
    os.environ['TORCH_HOME'] = '/tmp/torch'
    
    if len(sys.argv) != 2:
        print("❌ Usage: python detect.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    temp_image_path = None
    
    # ตรวจสอบไฟล์รูปภาพ
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    original_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    print(f"🖼️ Processing: {image_path} ({original_size_mb:.1f}MB)")
    
    try:
        # Import และโหลดโมเดล
        from ultralytics import YOLO
        
        # ลำดับโหลดโมเดล
        model_paths = [
            './yolov8/best_n.pt',
            './yolov8/best_m.pt',
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
        
        # ลดขนาดรูปหากจำเป็น
        processing_image_path, is_temp = resize_image_if_needed(image_path)
        if is_temp:
            temp_image_path = processing_image_path
        
        # เตรียมโฟลเดอร์ output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"runs/detect/predict_{timestamp}"
        
        # ทำ Detection พร้อม timeout เพิ่มเป็น 90 วินาที
        print("🔍 Running detection...")
        
        try:
            # ตั้ง timeout 90 วินาที สำหรับรูปใหญ่
            timeout_duration = 300 if original_size_mb > 3 else 90
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_duration)
            
            # ปรับการตั้งค่าให้เหมาะกับรูปใหญ่
            imgsz = 640 if original_size_mb < 3 else 1280
            max_det = 50 if original_size_mb < 5 else 100
            conf_threshold = 0.3 if original_size_mb < 2 else 0.25
            
            print(f"⚙️ Settings: imgsz={imgsz}, conf={conf_threshold}, max_det={max_det}, timeout={timeout_duration}s")
            
            results = model(
                processing_image_path,
                save=True,
                project='runs',
                name=f'detect/predict_{timestamp}',
                exist_ok=True,
                conf=conf_threshold,
                imgsz=imgsz,
                device='cpu',
                verbose=False,
                max_det=max_det,
                half=False,  # ปิด half precision สำหรับ CPU
                augment=False  # ปิด augmentation เพื่อประหยัดเวลา
            )
            
            signal.alarm(0)  # ปิด alarm
            print("✅ Detection completed!")
            
            # แสดงผลลัพธ์
            total_detections = 0
            detected_classes = {}
            
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    total_detections += len(result.boxes)
                    
                    # นับจำนวนแต่ละ class
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = model.names[class_id]
                        
                        if class_name not in detected_classes:
                            detected_classes[class_name] = []
                        detected_classes[class_name].append(confidence)
                    
                    # แสดงรายละเอียด top detections
                    sorted_boxes = sorted(result.boxes, key=lambda x: float(x.conf[0]), reverse=True)
                    for i, box in enumerate(sorted_boxes[:5]):  # แสดงแค่ 5 ตัวแรก
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = model.names[class_id]
                        print(f"  🎯 #{i+1}: {class_name} ({confidence:.1%})")
                    
                    if len(result.boxes) > 5:
                        print(f"  ... และอีก {len(result.boxes) - 5} detections")
            
            # สรุปผลลัพธ์
            if detected_classes:
                print(f"\n📊 Summary:")
                for class_name, confidences in detected_classes.items():
                    avg_conf = sum(confidences) / len(confidences)
                    print(f"  • {class_name}: {len(confidences)} objects (avg: {avg_conf:.1%})")
            
            print(f"🎉 Total: {total_detections} objects detected")
            
            # Backup ไฟล์
            backup_results(output_dir, image_path)
            
        except TimeoutError:
            print(f"⏰ Detection timeout ({timeout_duration}s) - using fallback")
            signal.alarm(0)
            fallback_copy(image_path)
            
        except Exception as e:
            print(f"❌ Detection error: {str(e)[:150]}...")
            fallback_copy(image_path)
        
        # ลบไฟล์ชั่วคราว
        if temp_image_path and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
            print("🗑️ Cleaned temp file")
            
    except ImportError:
        print("❌ Ultralytics not available - using fallback")
        fallback_copy(image_path)
    except Exception as e:
        print(f"❌ Error: {str(e)[:150]}...")
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