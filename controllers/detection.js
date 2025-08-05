const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const cloudinary = require("cloudinary").v2;

cloudinary.config({
    cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
    api_key: process.env.CLOUDINARY_API_KEY,
    api_secret: process.env.CLOUDINARY_API_SECRET,
});

exports.detectionImg = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No image file provided" });
        }

        const imagePath = req.file.path.replaceAll("\\", "/");
        console.log("📤 Uploaded image path:", imagePath);

        const python = spawn("python", ["yolov8/detect.py", imagePath]);

        let output = "";

        python.stdout.on("data", (data) => {
            output += data.toString();
        });

        python.stderr.on("data", (data) => {
            console.error(`stderr: ${data}`);
        });

        python.on("close", async (code) => {
            try {
                const detectPath = path.join(__dirname, "../runs/detect");

                const subDirs = fs.readdirSync(detectPath).sort((a, b) => {
                    return (
                        fs.statSync(path.join(detectPath, b)).mtimeMs -
                        fs.statSync(path.join(detectPath, a)).mtimeMs
                    );
                });

                const latestDir = subDirs[0];
                const resultDirPath = path.join(detectPath, latestDir);

                const resultFiles = fs.readdirSync(resultDirPath).filter(file =>
                    /\.(jpg|jpeg|png|webp)$/i.test(file)
                );

                if (resultFiles.length === 0) {
                    throw new Error("No image files found in result folder");
                }

                const resultImageFile = resultFiles[0];
                const resultImgPath = path.join(resultDirPath, resultImageFile);

                // ⬆️ Upload to Cloudinary
                const uploadResult = await cloudinary.uploader.upload(resultImgPath, {
                    folder: "detections"
                });

                console.log("🌐 Cloudinary URL:", uploadResult.secure_url);


                // ✅ ส่ง response ก่อน
                if (!res.headersSent) {
                    res.json({
                        result: output.trim(),
                        imageUrl: uploadResult.secure_url,
                    });
                }

                // 🧹 ลบภาพต้นฉบับที่อัปโหลดไว้ชั่วคราว
                fs.unlink(imagePath, (err) => {
                    if (err) {
                        console.error("❌ Failed to delete original uploaded image:", err);
                    } else {
                        console.log("🧹 Deleted original uploaded image:", imagePath);
                    }
                });

                // 🧹 ลบไฟล์หลังส่ง response แล้ว
                fs.rm(resultDirPath, { recursive: true, force: true }, (err) => {
                    if (err) {
                        console.error("Failed to delete detection result folder:", err);
                    } else {
                        console.log("🧹 Deleted detection folder:", resultDirPath);
                    }
                });

            } catch (err) {
                console.error("Error reading detection folder:", err);
                if (!res.headersSent) {
                    res.status(500).json({ error: "Detection folder read failed" });
                }
            }
        });
    } catch (error) {
        console.error("Internal server error:", error);
        if (!res.headersSent) {
            res.status(500).json({ error: "Internal server error" });
        }
    }
};



// const fs = require("fs");
// const path = require("path");
// const { spawn } = require("child_process");
// const cloudinary = require("cloudinary").v2;

// cloudinary.config({
//   cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
//   api_key: process.env.CLOUDINARY_API_KEY,
//   api_secret: process.env.CLOUDINARY_API_SECRET,
// });

// exports.detectionImg = async (req, res) => {
//     try {
//         if (!req.file) {
//             return res.status(400).json({ error: "No image file provided" });
//         }

//         const imagePath = req.file.path.replaceAll("\\", "/");
//         console.log("📤 Uploaded image path:", imagePath);

//         const python = spawn("python", ["yolov8/detect.py", imagePath]);

//         let output = "";

//         python.stdout.on("data", (data) => {
//             output += data.toString();
//         });

//         python.stderr.on("data", (data) => {
//             console.error(`stderr: ${data}`);
//         });

//         python.on("close", async (code) => {
//             try {
//                 const detectPath = path.join(__dirname, "../runs/detect");

//                 if (!fs.existsSync(detectPath)) {
//                     fs.mkdirSync(detectPath, { recursive: true });
//                 }

//                 const subDirs = fs.readdirSync(detectPath).sort((a, b) => {
//                     return (
//                         fs.statSync(path.join(detectPath, b)).mtimeMs -
//                         fs.statSync(path.join(detectPath, a)).mtimeMs
//                     );
//                 });

//                 const latestDir = subDirs[0];
//                 const resultDirPath = path.join(detectPath, latestDir);

//                 const resultFiles = fs.readdirSync(resultDirPath).filter(file =>
//                     /\.(jpg|jpeg|png|webp)$/i.test(file)
//                 );

//                 if (resultFiles.length === 0) {
//                     throw new Error("No image files found in result folder");
//                 }

//                 const resultImageFile = resultFiles[0];
//                 const resultImgPath = path.join(resultDirPath, resultImageFile);

//                 // 📤 Upload to Cloudinary
//                 const uploadResult = await cloudinary.uploader.upload(resultImgPath, {
//                     folder: "detections"
//                 });

//                 if (!res.headersSent) {
//                     res.json({
//                         result: output.trim(),
//                         imageUrl: uploadResult.secure_url, // ✅ ส่ง URL จาก Cloudinary กลับไป
//                     });
//                 }
//             } catch (err) {
//                 console.error("Error reading detection folder:", err);
//                 if (!res.headersSent) {
//                     res.status(500).json({ error: "Detection folder read failed" });
//                 }
//             }
//         });
//     } catch (error) {
//         console.error("Internal server error:", error);
//         if (!res.headersSent) {
//             res.status(500).json({ error: "Internal server error" });
//         }
//     }
// };
