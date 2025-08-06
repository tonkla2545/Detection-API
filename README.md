# 🦈 YOLOv8 Shark Detection Web App

เว็บแอปพลิเคชันที่สามารถอัปโหลดภาพและตรวจจับฉลามด้วยโมเดล YOLOv8 Nano  
พร้อมแสดงผลลัพธ์การตรวจจับบนหน้าเว็บแบบเรียลไทม์

---

## 📸 ความสามารถหลัก
- ✅ อัปโหลดภาพผ่านหน้าเว็บ
- 🧠 ประมวลผลด้วย YOLOv8 (`yolov8n`)
- 📦 แสดงผลการตรวจจับวัตถุในรูปภาพ
- 🦈 ตรวจจับเฉพาะฉลามสายพันธุ์ต่อไปนี้:
  - Blue Shark, Bull Shark, Mako Shark  
  - Sand Tiger Shark, White Shark, Whitetip Shark  
  - Hammerhead Shark, Nurse Shark, Tiger Shark, Whale Shark

> 📝 *หมายเหตุ: ใช้ YOLOv8n (Nano) เพื่อให้สามารถใช้งานบนเซิร์ฟเวอร์ฟรี เช่น Render/Vercel ได้รวดเร็ว*

---

## 🛠️ เทคโนโลยีที่ใช้

| Layer | Tech |
|-------|------|
| 🎨 Frontend | React.js, TailwindCSS, Framer Motion, React Icons |
| 🧪 Backend | Node.js, Express.js |
| 🧠 AI Model | [Ultralytics YOLOv8n](https://github.com/ultralytics/ultralytics) |
| ☁️ Hosting | Vercel (Frontend), Render (Backend) |

---

## 🚀 การติดตั้งและรันแอป (Local)
### Back End
```bash
cd server
npm install
pip install requirements.txt
node index.js

---

PORT=5000
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret