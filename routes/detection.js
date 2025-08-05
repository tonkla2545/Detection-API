const express = require("express");
const router = express.Router();
const multer = require('multer')
const upload = require('../configs/upload')

const { detectionImg } = require("../controllers/detection");

router.post("/detection", upload.single("image"), detectionImg);

module.exports = router;
