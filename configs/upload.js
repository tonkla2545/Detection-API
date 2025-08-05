// config/multer.js หรือที่คุณใช้กำหนด upload
const multer = require('multer')
const path = require('path')
const crypto = require('crypto')

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/')
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname) // ดึง .jpg, .png
    const name = crypto.randomBytes(16).toString('hex') + ext // ชื่อไฟล์ใหม่ + นามสกุล
    cb(null, name)
  }
})

const upload = multer({ storage })
module.exports = upload
