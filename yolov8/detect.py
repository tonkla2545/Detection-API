import sys
import os
import shutil
import time
import signal
from datetime import datetime
from PIL import Image

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Detection timeout!")

def resize_image_if_needed(image_path, max_size_mb=2, max_dimension=1280):
    try:
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb <= max_size_mb:
            return image_path, False

        temp_path = f"/tmp/resized_{int(time.time())}.jpg"
        with Image.open(image_path) as img:
            width, height = img.size
            if max(width, height) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(temp_path, 'JPEG', quality=85, optimize=True)
        return temp_path, True
    except Exception:
        return image_path, False

def load_model():
    from ultralytics import YOLO
    for path in ['./yolov8/best_n.pt']:
        if os.path.exists(path) or path.endswith('n.pt'):
            try:
                return YOLO(path)
            except: pass
    return None

def run_detection(model, img_path, out_dir, conf, imgsz, max_det, timeout):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    results = model(img_path, save=True, project='runs', name=out_dir,
                    exist_ok=True, conf=conf, imgsz=imgsz, device='cpu', 
                    verbose=False, max_det=max_det, half=False, augment=False)
    signal.alarm(0)
    return results

def summarize(results, model):
    summary = {}
    total = 0
    for result in results:
        if hasattr(result, 'boxes') and result.boxes:
            total += len(result.boxes)
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                name = model.names[cls]
                summary.setdefault(name, []).append(conf)
    print(f"\n📊 Total: {total} detections")
    for name, confs in summary.items():
        avg = sum(confs)/len(confs)
        print(f"  • {name}: {len(confs)} (avg: {avg:.1%})")

def backup_output(out_dir, orig_path):
    try:
        src = os.path.join(os.getcwd(), out_dir)
        images = [f for f in os.listdir(src) if f.lower().endswith(('jpg', 'jpeg', 'png'))]
        if images:
            os.makedirs('runs/detect', exist_ok=True)
            shutil.copy2(os.path.join(src, images[0]), os.path.join('runs/detect', os.path.basename(orig_path)))
            return True
    except: pass
    return False

def fallback(image_path):
    try:
        ts = int(time.time())
        dst = f'runs/detect/predict{ts}'
        os.makedirs(dst, exist_ok=True)
        os.makedirs('runs/detect', exist_ok=True)
        filename = os.path.basename(image_path)
        shutil.copy2(image_path, os.path.join(dst, filename))
        shutil.copy2(image_path, os.path.join('runs/detect', filename))
    except: pass

def main():
    os.environ.update({
        'YOLO_CONFIG_DIR': '/tmp',
        'ULTRALYTICS_CONFIG_DIR': '/tmp',
        'TORCH_HOME': '/tmp/torch'
    })

    if len(sys.argv) != 2:
        print("❌ Usage: python detect.py <image_path>")
        return

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"❌ Image not found: {img_path}")
        return

    print(f"🖼️ Processing: {img_path}")
    size_mb = os.path.getsize(img_path) / (1024 * 1024)
    img_path, temp = resize_image_if_needed(img_path)

    model = load_model()
    if not model:
        print("❌ No model loaded")
        fallback(img_path)
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = f"detect/predict_{ts}"

    try:
        timeout = 300 if size_mb > 3 else 90
        imgsz = 640 if size_mb < 3 else 1280
        conf = 0.3 if size_mb < 2 else 0.25
        max_det = 50 if size_mb < 5 else 100

        print(f"⚙️ Running detection with imgsz={imgsz}, conf={conf}, max_det={max_det}, timeout={timeout}s")
        results = run_detection(model, img_path, out_dir, conf, imgsz, max_det, timeout)
        summarize(results, model)
        backup_output(f"runs/{out_dir}", sys.argv[1])
    except TimeoutError:
        print(f"⏰ Detection timed out")
        fallback(img_path)
    except Exception as e:
        print(f"❌ Detection error: {str(e)[:150]}...")
        fallback(img_path)
    finally:
        if temp and os.path.exists(img_path):
            os.unlink(img_path)

if __name__ == "__main__":
    main()
