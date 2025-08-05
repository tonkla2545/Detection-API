import sys
import os
import shutil
from PIL import Image, ImageDraw

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
        
        # ลองใช้ YOLOv8 จริง
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
            
        except ImportError as e:
            print(f"⚠️ Cannot import ultralytics: {e}")
            print("🎨 Using fallback: creating dummy detection result...")
            
            # สร้างรูปปลอมสำหรับทดสอบ (ถ้า YOLO ไม่มี)
            try:
                # เปิดรูปต้นฉบับ
                with Image.open(image_path) as img:
                    # สร้างสำเนา
                    result_img = img.copy()
                    draw = ImageDraw.Draw(result_img)
                    
                    # วาดกรอบสี่เหลี่ยมปลอม (dummy detection)
                    width, height = img.size
                    draw.rectangle([width//4, height//4, 3*width//4, 3*height//4], 
                                 outline="red", width=3)
                    
                    # บันทึกรูปผลลัพธ์
                    result_filename = os.path.basename(image_path)
                    result_path = os.path.join(result_dir, result_filename)
                    result_img.save(result_path)
                    
                    print(f"💾 Saved dummy result to: {result_path}")
                    print("✅ Dummy detection completed")
                    
            except Exception as img_error:
                print(f"❌ Error creating dummy result: {img_error}")
                # ถ้าสร้างรูปไม่ได้ ก็แค่คัดลอกไฟล์เดิม
                result_filename = os.path.basename(image_path)
                result_path = os.path.join(result_dir, result_filename)
                shutil.copy2(image_path, result_path)
                print(f"📋 Copied original image to: {result_path}")
        
        except Exception as yolo_error:
            print(f"❌ YOLO detection failed: {yolo_error}")
            sys.exit(1)
        
        # แสดงไฟล์ในโฟลเดอร์ผลลัพธ์
        if os.path.exists(result_dir):
            files = os.listdir(result_dir)
            print(f"📂 Files in result directory: {files}")
        
        print("🎉 Script completed successfully")
        
    except Exception as e:
        print(f"❌ Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()